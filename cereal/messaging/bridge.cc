#include <cassert>

#include "cereal/messaging/msgq_to_zmq.h"
#include "cereal/services.h"
#include "common/util.h"

ExitHandler do_exit;

static std::vector<std::string> get_services(const std::string &whitelist_str, bool zmq_to_msgq) {
  // A non-empty whitelist filters in both directions. This matters for msgq_to_zmq
  // (forward, device -> remote subscriber): with no filter it forwards every service,
  // camera frames included, which can spike memory enough to SIGBUS other processes
  // touching their /dev/shm msgq segments on a device with no swap. See git log.
  (void)zmq_to_msgq;
  std::vector<std::string> service_list;
  for (const auto& it : services) {
    std::string name = it.second.name;
    bool in_whitelist = whitelist_str.find(name) != std::string::npos;
    if (!whitelist_str.empty() && !in_whitelist) {
      continue;
    }
    service_list.push_back(name);
  }
  return service_list;
}

void msgq_to_zmq(const std::vector<std::string> &endpoints, const std::string &ip) {
  MsgqToZmq bridge;
  bridge.run(endpoints, ip);
}

void zmq_to_msgq(const std::vector<std::string> &endpoints, const std::string &ip) {
  auto poller = std::make_unique<ZMQPoller>();
  auto pub_context = std::make_unique<MSGQContext>();
  auto sub_context = std::make_unique<ZMQContext>();
  std::map<SubSocket *, PubSocket *> sub2pub;

  for (auto endpoint : endpoints) {
    auto pub_sock = new MSGQPubSocket();
    auto sub_sock = new ZMQSubSocket();
    pub_sock->connect(pub_context.get(), endpoint);
    sub_sock->connect(sub_context.get(), endpoint, ip, false);

    poller->registerSocket(sub_sock);
    sub2pub[sub_sock] = pub_sock;
  }

  while (!do_exit) {
    for (auto sub_sock : poller->poll(100)) {
      std::unique_ptr<Message> msg(sub_sock->receive(true));
      if (msg) {
        sub2pub[sub_sock]->sendMessage(msg.get());
      }
    }
  }

  // Clean up allocated sockets
  for (auto &[sub_sock, pub_sock] : sub2pub) {
    delete sub_sock;
    delete pub_sock;
  }
}

int main(int argc, char **argv) {
  bool is_zmq_to_msgq = argc > 2;
  std::string ip = is_zmq_to_msgq ? argv[1] : "127.0.0.1";
  // Forward mode (no reverse ip given) now also accepts an optional single argument:
  // a comma-separated service whitelist, e.g. `./bridge can,carState,carControl`.
  // With no argument at all, behavior is unchanged (forwards everything).
  std::string whitelist_str = is_zmq_to_msgq ? std::string(argv[2]) : (argc > 1 ? std::string(argv[1]) : "");
  std::vector<std::string> endpoints = get_services(whitelist_str, is_zmq_to_msgq);

  if (is_zmq_to_msgq) {
    zmq_to_msgq(endpoints, ip);
  } else {
    msgq_to_zmq(endpoints, ip);
  }
  return 0;
}
