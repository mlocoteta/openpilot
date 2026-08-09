#include "starpilot/ui/qt/offroad/model_settings.h"
#include "starpilot/ui/qt/offroad/expandable_multi_option_dialog.h"
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QDoubleSpinBox>
#include <QPushButton>
#include <QDialog>
#include <algorithm>

#include "system/hardware/hw.h"

namespace {

QString paramDefaultValue(const Params &params, const char *key) {
  return QString::fromStdString(const_cast<Params &>(params).getKeyDefaultValue(key).value_or("")).trimmed();
}

QString builtinDefaultModelKey(const Params &params) {
  QString key = paramDefaultValue(params, "Model");
  if (key.isEmpty()) {
    key = paramDefaultValue(params, "DrivingModel");
  }
  return key.isEmpty() ? QStringLiteral("rdf") : key;
}

QString builtinDefaultModelName(const Params &params) {
  QString name = paramDefaultValue(params, "DrivingModelName");
  return name.isEmpty() ? QStringLiteral("Regret Driven Framework") : name;
}

QStringList builtinDefaultModelAliases(const QString &defaultKey) {
  QString canonical = defaultKey.trimmed();
  if (canonical.isEmpty()) {
    canonical = QStringLiteral("rdf");
  }

  QStringList aliases{canonical};

  if (canonical.endsWith("2")) {
    aliases.append(canonical.left(canonical.size() - 1));
  } else {
    aliases.append(canonical + "2");
  }

  if (canonical.endsWith("_default")) {
    aliases.append(canonical.left(canonical.size() - QStringLiteral("_default").size()));
  }

  aliases.removeAll("");
  aliases.removeDuplicates();
  return aliases;
}

bool isBuiltinDefaultModel(const Params &params, const QString &key) {
  return builtinDefaultModelAliases(builtinDefaultModelKey(params)).contains(key.trimmed());
}

QString canonicalModelKey(const Params &params, const QString &key) {
  const QString trimmedKey = key.trimmed();
  return isBuiltinDefaultModel(params, trimmedKey) ? builtinDefaultModelKey(params) : trimmedKey;
}

void ensureDefaultModelVisible(const Params &params, const QString &fallbackSeries,
                               QMap<QString, QString> &modelFileToNameMap,
                               QMap<QString, QString> &modelFileToNameMapProcessed,
                               QMap<QString, QString> &modelSeriesMap,
                               QMap<QString, QString> &modelReleasedDates) {
  const QString defaultKey = builtinDefaultModelKey(params);
  QString displayName = builtinDefaultModelName(params);
  QString series = fallbackSeries;
  QString releasedDate;

  for (const QString &alias : builtinDefaultModelAliases(defaultKey)) {
    if (!modelFileToNameMap.contains(alias)) {
      continue;
    }

    displayName = modelFileToNameMap.value(alias, displayName);
    if (series == fallbackSeries && modelSeriesMap.contains(alias)) {
      series = modelSeriesMap.value(alias);
    }
    if (releasedDate.isEmpty() && modelReleasedDates.contains(alias)) {
      releasedDate = modelReleasedDates.value(alias);
    }

    if (alias != defaultKey) {
      modelFileToNameMap.remove(alias);
      modelFileToNameMapProcessed.remove(alias);
      modelSeriesMap.remove(alias);
      modelReleasedDates.remove(alias);
    }
  }

  modelFileToNameMap.insert(defaultKey, displayName);
  modelFileToNameMapProcessed.insert(defaultKey, cleanModelName(displayName));
  modelSeriesMap.insert(defaultKey, series);
  if (!releasedDate.isEmpty()) {
    modelReleasedDates.insert(defaultKey, releasedDate);
  }
}

}  // namespace

StarPilotModelPanel::StarPilotModelPanel(StarPilotSettingsWindow *parent) : StarPilotListWidget(parent),
                                                                             allModelsDownloaded(false),
                                                                             allModelsDownloading(false),
                                                                             cancellingDownload(false),
                                                                             finalizingDownload(false),
                                                                             forceOpenDescriptions(false),
                                                                             modelDownloading(false),
                                                                             noModelsDownloaded(true),
                                                                             started(false),
                                                                             tinygradUpdate(false),
                                                                             updatingTinygrad(false),
                                                                             tuningLevel(0),
                                                                             parent(parent) {
  if (Hardware::PC()) {
    modelDir.setPath(QString::fromStdString(Path::comma_home() + "/starpilot/data/models/"));
  }
  modelDir.mkpath(".");

  QStackedLayout *modelLayout = new QStackedLayout();
  addItem(modelLayout);

  StarPilotListWidget *modelList = new StarPilotListWidget(this);

  ScrollView *modelPanel = new ScrollView(modelList, this);

  modelLayout->addWidget(modelPanel);

  StarPilotListWidget *modelLabelsList = new StarPilotListWidget(this);

  ScrollView *modelLabelsPanel = new ScrollView(modelLabelsList, this);

  modelLayout->addWidget(modelLabelsPanel);

  const std::vector<std::tuple<QString, QString, QString, QString>> modelToggles {
    {"AutomaticallyDownloadModels", tr("Automatically Download New Models"), tr("Automatically download new driving models as they become available."), ""},
    {"DeleteModel", tr("Delete Driving Models"), tr("Delete driving models from the device."), ""},
    {"DownloadModel", tr("Download Driving Models"), tr("Download driving models to the device."), ""},
    {"ModelRandomizer", tr("Model Randomizer"), tr("Driving models are chosen at random each drive and feedback prompts are used to find the model that best suits your needs."), ""},
    {"RecoveryPower", tr("Recovery Power"), tr("Adjust the strength of planplus lane recovery corrections (0.5 to 2.0)."), ""},
    {"ManageBlacklistedModels", tr("Manage Model Blacklist"), tr("Add or remove models from the <b>Model Randomizer</b>'s blacklist list."), ""},
    {"ManageScores", tr("Manage Model Ratings"), tr("Reset or view the saved ratings for the driving models."), ""},
    {"SelectModel", tr("Select Driving Model"), tr("Select the active driving model."), ""},
  };

  StarPilotParamValueButtonControl *recoveryPowerToggle = nullptr;

  for (const auto &[param, title, desc, icon] : modelToggles) {
    AbstractControl *modelToggle;

    if (param == "DeleteModel") {
      deleteModelButton = new StarPilotButtonsControl(title, desc, icon, {tr("DELETE"), tr("DELETE ALL")});
      QObject::connect(deleteModelButton, &StarPilotButtonsControl::buttonClicked, [this](int id) {
        QMap<QString, QString> deletableModelsMap = getDeletableModelDisplayNames();
        noModelsDownloaded = deletableModelsMap.isEmpty();

        if (noModelsDownloaded) {
          return;
        }

        if (id == 0) {
          // Group deletable models by series and keep a lookup for selected names
          QMap<QString, QStringList> deletableSeriesToModels;
          QMap<QString, QString> displayNameToKey;
          QMap<QString, QString> deletableFileToNameMap;
          for (auto it = deletableModelsMap.constBegin(); it != deletableModelsMap.constEnd(); ++it) {
            const QString &modelKey = it.key();
            const QString &displayName = it.value();
            QString series = modelSeriesMap.value(modelKey, tr("Custom Series"));
            deletableSeriesToModels[series].append(displayName);
            displayNameToKey.insert(displayName, modelKey);
            deletableFileToNameMap.insert(modelKey, displayName);
          }

          // Sort models within each series
          for (QString &series : deletableSeriesToModels.keys()) {
            QStringList &models = deletableSeriesToModels[series];
            models.removeDuplicates();
            std::sort(models.begin(), models.end());
          }

          QString savedSortMode = QString::fromStdString(params.get("ModelSortMode"));
          if (savedSortMode.isEmpty()) savedSortMode = "alphabetical";

          QString modelToDelete = ExpandableMultiOptionDialog::getSelection(tr("Select a driving model to delete"), deletableSeriesToModels, "", this,
                                                                           QStringList(), QStringList(), QMap<QString, QString>(),
                                                                           deletableFileToNameMap, savedSortMode);
          if (!modelToDelete.isEmpty()) {
            QString modelKey = displayNameToKey.value(modelToDelete);
            if (modelKey.isEmpty()) {
              QString processedName = cleanModelName(modelToDelete);
              for (auto it = deletableModelsMap.constBegin(); it != deletableModelsMap.constEnd(); ++it) {
                if (cleanModelName(it.value()) == processedName) {
                  modelKey = it.key();
                  break;
                }
              }
            }

            if (!modelKey.isEmpty() && ConfirmationDialog::confirm(tr("Are you sure you want to delete the \"%1\" model?").arg(modelToDelete), tr("Delete"), this)) {
              for (const QString &file : modelDir.entryList(QDir::Files)) {
                QString base = QFileInfo(file).baseName();
                if (base.startsWith(modelKey)) {
                  QFile::remove(modelDir.filePath(file));
                }
              }

              allModelsDownloaded = false;
              noModelsDownloaded = getDeletableModelDisplayNames().isEmpty();
              deleteModelButton->setEnabled(!(allModelsDownloading || modelDownloading || noModelsDownloaded));
            }
          }
        } else if (id == 1) {
          if (ConfirmationDialog::confirm(tr("Are you sure you want to delete all of your downloaded driving models?"), tr("Delete"), this)) {
            const QList<QString> deletableKeys = deletableModelsMap.keys();
            for (const QString &file : modelDir.entryList(QDir::Files)) {
              QString base = QFileInfo(file).baseName();
              for (const QString &modelKey : deletableKeys) {
                if (base.startsWith(modelKey)) {
                  QFile::remove(modelDir.filePath(file));
                  break;
                }
              }
            }

            allModelsDownloaded = false;
            noModelsDownloaded = true;
            deleteModelButton->setEnabled(false);
          }
        }
      });
      modelToggle = deleteModelButton;
    } else if (param == "DownloadModel") {
      downloadModelButton = new StarPilotButtonsControl(title, desc, icon, {tr("DOWNLOAD"), tr("DOWNLOAD ALL")});
      QObject::connect(downloadModelButton, &StarPilotButtonsControl::buttonClicked, [this](int id) {
        if (id == 0) {
          if (modelDownloading) {
            params_memory.putBool("CancelModelDownload", true);

            cancellingDownload = true;
        } else {
          QMap<QString, QStringList> downloadableSeriesToModels;
          QStringList downloadableModelNames;

          for (auto it = modelFileToNameMap.constBegin(); it != modelFileToNameMap.constEnd(); ++it) {
            const QString &modelKey = it.key();
            const QString &modelName = it.value();
            if (modelName.isEmpty() || isModelInstalled(modelKey)) {
              continue;
            }

            QString series = modelSeriesMap.value(modelKey, tr("Custom Series"));
            downloadableSeriesToModels[series].append(modelName);
            if (!downloadableModelNames.contains(modelName)) {
              downloadableModelNames.append(modelName);
            }
          }

          allModelsDownloaded = downloadableModelNames.isEmpty();
          if (allModelsDownloaded) {
            return;
          }

          for (QString &series : downloadableSeriesToModels.keys()) {
            QStringList &models = downloadableSeriesToModels[series];
            models.removeDuplicates();
            std::sort(models.begin(), models.end());
          }

          QStringList userFavorites = QString::fromStdString(params.get("UserFavorites")).split(",");
          userFavorites.removeAll("");

          QStringList communityFavorites = QString::fromStdString(params.get("CommunityFavorites")).split(",");
          communityFavorites.removeAll("");

          QString savedSortMode = QString::fromStdString(params.get("ModelSortMode"));
          if (savedSortMode.isEmpty()) savedSortMode = "alphabetical";

          ExpandableMultiOptionDialog dialog(
              tr("Select a driving model to download"),
              downloadableSeriesToModels,
              "",
              this,
              userFavorites,
              communityFavorites,
              modelReleasedDates,
              modelFileToNameMap,
              savedSortMode);

          int dialogResult = dialog.exec();

          QString sortMode = dialog.getCurrentSortMode();
          QStringList newUserFavs = dialog.getUserFavorites();
          params.put("ModelSortMode", sortMode.toStdString());
          params.put("UserFavorites", newUserFavs.join(",").toStdString());
          userFavorites = newUserFavs;

          if (dialogResult == QDialog::Accepted) {
            QString modelToDownload = dialog.selection;
            if (!modelToDownload.isEmpty()) {
              QString modelKey = modelFileToNameMap.key(modelToDownload);
              params_memory.put("ModelToDownload", modelKey.toStdString());
              // Also persist the version for this downloaded model if known
              {
                QFile vf(modelDir.filePath(".model_versions.json"));
                if (vf.open(QIODevice::ReadOnly)) {
                  auto doc = QJsonDocument::fromJson(vf.readAll());
                  if (doc.isObject()) {
                    auto obj = doc.object();
                    if (obj.contains(modelKey)) {
                      const std::string version = obj.value(modelKey).toString().toStdString();
                      params.put("ModelVersion", version);
                      params.put("DrivingModelVersion", version);
                    }
                  }
                }
              }
                params_memory.put("ModelDownloadProgress", "Downloading...");

                downloadModelButton->setText(0, tr("CANCEL"));

                downloadModelButton->setValue("Downloading...");

                downloadModelButton->setVisibleButton(1, false);

                modelDownloading = true;
              }
            }
          }
        } else if (id == 1) {
          if (allModelsDownloading) {
            params_memory.putBool("CancelModelDownload", true);

            cancellingDownload = true;
          } else {
            params_memory.putBool("DownloadAllModels", true);
            params_memory.put("ModelDownloadProgress", "Downloading...");

            downloadModelButton->setText(1, tr("CANCEL"));

            downloadModelButton->setValue("Downloading...");

            downloadModelButton->setVisibleButton(0, false);

            allModelsDownloading = true;
          }
        }
      });
      modelToggle = downloadModelButton;
    } else if (param == "ManageBlacklistedModels") {
      StarPilotButtonsControl *blacklistBtn = new StarPilotButtonsControl(title, desc, icon, {tr("ADD"), tr("REMOVE"), tr("REMOVE ALL")});
      QObject::connect(blacklistBtn, &StarPilotButtonsControl::buttonClicked, [this](int id) {
        QStringList blacklistedModels = QString::fromStdString(params.get("BlacklistedModels")).split(",");
        blacklistedModels.removeAll("");

        if (id == 0) {
          QStringList blacklistableModels;
          for (const QString &model : modelFileToNameMapProcessed.keys()) {
            if (!blacklistedModels.contains(model)) {
              blacklistableModels.append(modelFileToNameMapProcessed.value(model));
            }
          }

          if (blacklistableModels.size() <= 1) {
            ConfirmationDialog::alert(tr("There are no more models to blacklist! The only available model is \"%1\"!").arg(blacklistableModels.first()), this);
          } else {
            // Group blacklistable models by series
            QMap<QString, QStringList> blacklistableSeriesToModels;
            for (const QString &modelName : blacklistableModels) {
              QString modelKey = modelFileToNameMapProcessed.key(modelName);
              QString series = modelSeriesMap.value(modelKey, "Custom Series");
              blacklistableSeriesToModels[series].append(modelName);
            }

            // Sort models within each series
            for (QString &series : blacklistableSeriesToModels.keys()) {
              blacklistableSeriesToModels[series].sort();
            }

            QString modelToBlacklist = ExpandableMultiOptionDialog::getSelection(tr("Select a model to add to the blacklist"), blacklistableSeriesToModels, "", this);
            if (!modelToBlacklist.isEmpty()) {
              if (ConfirmationDialog::confirm(tr("Are you sure you want to add the \"%1\" model to the blacklist?").arg(modelToBlacklist), tr("Add"), this)) {
                blacklistedModels.append(modelFileToNameMapProcessed.key(modelToBlacklist));

                params.put("BlacklistedModels", blacklistedModels.join(",").toStdString());
              }
            }
          }
        } else if (id == 1) {
          QStringList whitelistableModels;
          for (const QString &model : blacklistedModels) {
            QString modelName = modelFileToNameMapProcessed.value(model);
            whitelistableModels.append(modelName);
          }

          // Group whitelistable models by series
          QMap<QString, QStringList> whitelistableSeriesToModels;
          for (const QString &modelName : whitelistableModels) {
            QString modelKey = modelFileToNameMapProcessed.key(modelName);
            QString series = modelSeriesMap.value(modelKey, "Custom Series");
            whitelistableSeriesToModels[series].append(modelName);
          }

          // Sort models within each series
          for (QString &series : whitelistableSeriesToModels.keys()) {
            whitelistableSeriesToModels[series].sort();
          }

          QString modelToWhitelist = ExpandableMultiOptionDialog::getSelection(tr("Select a model to remove from the blacklist"), whitelistableSeriesToModels, "", this);
          if (!modelToWhitelist.isEmpty()) {
            if (ConfirmationDialog::confirm(tr("Are you sure you want to remove the \"%1\" model from the blacklist?").arg(modelToWhitelist), tr("Remove"), this)) {
              blacklistedModels.removeAll(modelFileToNameMapProcessed.key(modelToWhitelist));

              params.put("BlacklistedModels", blacklistedModels.join(",").toStdString());
            }
          }
        } else if (id == 2) {
          if (StarPilotConfirmationDialog::yesorno(tr("Are you sure you want to remove all of your blacklisted models?"), this)) {
            params.remove("BlacklistedModels");
          }
        }
      });
      modelToggle = blacklistBtn;
    } else if (param == "ManageScores") {
      StarPilotButtonsControl *manageScoresBtn = new StarPilotButtonsControl(title, desc, icon, {tr("RESET"), tr("VIEW")});
      QObject::connect(manageScoresBtn, &StarPilotButtonsControl::buttonClicked, [this, modelLayout, modelLabelsList, modelLabelsPanel](int id) {
        if (id == 0) {
          if (StarPilotConfirmationDialog::yesorno(tr("Are you sure you want to reset all of your model drives and scores?"), this)) {
            params.remove("ModelDrivesAndScores");
          }
        } else if (id == 1) {
          openSubPanel();

          updateModelLabels(modelLabelsList);

          modelLayout->setCurrentWidget(modelLabelsPanel);
        }
      });
      modelToggle = manageScoresBtn;
    } else if (param == "SelectModel") {
      selectModelButton = new ButtonControl(title, tr("SELECT"), desc);
      QObject::connect(selectModelButton, &ButtonControl::clicked, [this]() {
        // Group models by series for the enhanced dialog
        QMap<QString, QStringList> seriesToModels;
        QMap<QString, QString> installedModelFileToNameMap;
        QMap<QString, QString> installedReleasedDates;

        // Add all available models by series
        for (const QString &modelKey : modelFileToNameMap.keys()) {
          if (!isModelInstalled(modelKey)) {
            continue;
          }

          QString modelName = modelFileToNameMap.value(modelKey);
          installedModelFileToNameMap.insert(modelKey, modelName);
          if (modelReleasedDates.contains(modelKey)) {
            installedReleasedDates.insert(modelKey, modelReleasedDates.value(modelKey));
          }

          QString series = modelSeriesMap.value(modelKey, "Custom Series");
          seriesToModels[series].append(modelName);
        }

        // Sort models alphabetically within each series
        for (QString &series : seriesToModels.keys()) {
          seriesToModels[series].sort();
        }

        // Add default model to the beginning of its series
        const QString defaultKey = builtinDefaultModelKey(params);
        const QString defaultName = modelFileToNameMap.value(defaultKey, builtinDefaultModelName(params));
        const QString defaultSeries = modelSeriesMap.value(defaultKey, tr("Custom Series"));
        if (seriesToModels.contains(defaultSeries) && seriesToModels[defaultSeries].contains(defaultName)) {
          seriesToModels[defaultSeries].removeAll(defaultName);
          seriesToModels[defaultSeries].prepend(defaultName);
        }

        // Prepare favorites and dates for the enhanced dialog
        QStringList userFavs = QString::fromStdString(params.get("UserFavorites")).split(",");
        userFavs.removeAll("");

        QStringList communityFavs = QString::fromStdString(params.get("CommunityFavorites")).split(",");
        communityFavs.removeAll("");

        // Create dialog instance to access sort mode and favorites after selection
        QString savedSortMode = QString::fromStdString(params.get("ModelSortMode"));
        if (savedSortMode.isEmpty()) savedSortMode = "alphabetical";

        ExpandableMultiOptionDialog dialog(tr("Select a model - 🗺️ = Navigation | 📡 = Radar | 👀 = VOACC"),
                                          seriesToModels, currentModel, this,
                                          userFavs, communityFavs, installedReleasedDates, installedModelFileToNameMap, savedSortMode);

        int dialogResult = dialog.exec();

        // Persist sort mode and user favorites even if no selection was made
        QString sortMode = dialog.getCurrentSortMode();
        QStringList newUserFavs = dialog.getUserFavorites();
        params.put("ModelSortMode", sortMode.toStdString());
        params.put("UserFavorites", newUserFavs.join(",").toStdString());

        if (dialogResult == QDialog::Accepted) {
          QString modelToSelect = dialog.selection;
          if (!modelToSelect.isEmpty()) {
            currentModel = modelToSelect;

            QString modelKey = modelFileToNameMap.key(modelToSelect);
            params.put("Model", modelKey.toStdString());
            params.put("DrivingModel", modelKey.toStdString());
            params.put("DrivingModelName", modelToSelect.toStdString());
            // Sync ModelVersion with the selected model if known
            {
              QFile vf(modelDir.filePath(".model_versions.json"));
              if (vf.open(QIODevice::ReadOnly)) {
                auto doc = QJsonDocument::fromJson(vf.readAll());
                if (doc.isObject()) {
                  auto obj = doc.object();
                  if (obj.contains(modelKey)) {
                    const std::string version = obj.value(modelKey).toString().toStdString();
                    params.put("ModelVersion", version);
                    params.put("DrivingModelVersion", version);
                  }
                }
              }
            }

            updateStarPilotToggles();

            if (started) {
              if (StarPilotConfirmationDialog::toggleReboot(this)) {
                Hardware::reboot();
              }
            }
            selectModelButton->setValue(modelToSelect);

            noModelsDownloaded = getDeletableModelDisplayNames().isEmpty();
            deleteModelButton->setEnabled(!(allModelsDownloading || modelDownloading || noModelsDownloaded));
          }
        }
      });
      modelToggle = selectModelButton;

    } else if (param == "RecoveryPower") {
      std::vector<QString> recoveryPowerButton{"Reset"};
      modelToggle = new StarPilotParamValueButtonControl(param, title, desc, icon, 0.5, 2.0, QString(), std::map<float, QString>(), 0.1, false, {}, recoveryPowerButton, false, false);
      recoveryPowerToggle = static_cast<StarPilotParamValueButtonControl*>(modelToggle);
    } else {
      modelToggle = new ParamControl(param, title, desc, icon);
    }

    toggles[param] = modelToggle;

    modelList->addItem(modelToggle);

    QObject::connect(modelToggle, &AbstractControl::showDescriptionEvent, [this]() {
      update();
    });
  }

  QObject::connect(static_cast<ToggleControl*>(toggles["ModelRandomizer"]), &ToggleControl::toggleFlipped, [this](bool state) {
    updateToggles();

    if (state && !allModelsDownloaded) {
      if (StarPilotConfirmationDialog::yesorno(tr("The \"Model Randomizer\" only works with downloaded models. Do you want to download all the driving models?"), this)) {
        params_memory.putBool("DownloadAllModels", true);
        params_memory.put("ModelDownloadProgress", "Downloading...");

        downloadModelButton->setValue("Downloading...");

        allModelsDownloading = true;
      }
    }
  });

  if (recoveryPowerToggle) {
    QObject::connect(recoveryPowerToggle, &StarPilotParamValueButtonControl::buttonClicked, [this, recoveryPowerToggle]() {
      if (ConfirmationDialog::confirm(tr("Are you sure you want to reset your <b>Recovery Power</b> to the default of 1.0?"), tr("Reset"), this)) {
        params.putFloat("RecoveryPower", 1.0);
        recoveryPowerToggle->refresh();
        updateStarPilotToggles();
      }
    });
  }

  QObject::connect(parent, &StarPilotSettingsWindow::closeSubPanel, [modelLayout, modelPanel] {modelLayout->setCurrentWidget(modelPanel);});
  QObject::connect(uiState(), &UIState::uiUpdate, this, &StarPilotModelPanel::updateState);
}

bool StarPilotModelPanel::isModelInstalled(const QString &key) const {
  if (key.isEmpty()) {
    return false;
  }

  if (isBuiltinDefaultModel(params, key)) {
    return true;
  }

  bool has_combined_tg = false;

  for (const QString &file : modelDir.entryList(QDir::Files)) {
    QFileInfo fi(modelDir.filePath(file));
    const QString base = fi.baseName();
    const QString ext = fi.suffix();

    if (!(base.startsWith(key) || base.startsWith(key + "_"))) continue;
    if (ext == "pkl" && base == key + "_driving_tinygrad") {
      has_combined_tg = true;
    }
  }

  return has_combined_tg;
}

QMap<QString, QString> StarPilotModelPanel::getDeletableModelDisplayNames() {
  QMap<QString, QString> deletable;

  const QString defaultKey = builtinDefaultModelKey(params);
  const QString defaultName = modelFileToNameMap.value(defaultKey, builtinDefaultModelName(params));
  const QString processedDefault = cleanModelName(defaultName);
  QString processedCurrent = cleanModelName(currentModel);

  for (auto it = modelFileToNameMap.constBegin(); it != modelFileToNameMap.constEnd(); ++it) {
    const QString &modelKey = it.key();
    const QString &displayName = it.value();
    if (displayName.isEmpty()) {
      continue;
    }

    if (!isModelInstalled(modelKey)) {
      continue;
    }

    QString processedName = cleanModelName(displayName);
    if (!processedCurrent.isEmpty() && processedName == processedCurrent) {
      continue;
    }

    if (!processedDefault.isEmpty() && processedName == processedDefault) {
      continue;
    }

    deletable.insert(modelKey, displayName);
  }

  return deletable;
}

void StarPilotModelPanel::showEvent(QShowEvent *event) {
  StarPilotUIState &fs = *starpilotUIState();
  UIState &s = *uiState();

  starpilotToggleLevels = parent->starpilotToggleLevels;
  tuningLevel = parent->tuningLevel;

  allModelsDownloading = params_memory.getBool("DownloadAllModels");
  modelDownloading = !params_memory.get("ModelToDownload").empty();

  QStringList availableModels = QString::fromStdString(params.get("AvailableModels")).split(",");
  availableModelNames = QString::fromStdString(params.get("AvailableModelNames")).split(",");
  availableModelSeries = QString::fromStdString(params.get("AvailableModelSeries")).split(",");
  QStringList releasedDatesParam = QString::fromStdString(params.get("ModelReleasedDates")).split(",");
  QStringList communityFavsParam = QString::fromStdString(params.get("CommunityFavorites")).split(",");
  QStringList userFavsParam = QString::fromStdString(params.get("UserFavorites")).split(",");

  // Build a simple model->version map for quick lookups elsewhere
  {
    QStringList versionList = QString::fromStdString(params.get("ModelVersions")).split(",");
    QJsonObject versionObj;
    int verCount = qMin(availableModels.size(), versionList.size());
    for (int i = 0; i < verCount; ++i) {
      const QString modelKey = canonicalModelKey(params, availableModels[i]);
      if (!modelKey.isEmpty()) {
        versionObj.insert(modelKey, versionList[i]);
      }
    }
    QFile out(modelDir.filePath(".model_versions.json"));
    if (out.open(QIODevice::WriteOnly)) {
      out.write(QJsonDocument(versionObj).toJson());
      out.close();
    }
  }

  modelFileToNameMap.clear();
  modelFileToNameMapProcessed.clear();
  modelSeriesMap.clear();
  modelReleasedDates.clear();
  int size = qMin(availableModels.size(), availableModelNames.size());
  for (int i = 0; i < size; ++i) {
    const QString modelKey = canonicalModelKey(params, availableModels[i]);
    const QString modelName = availableModelNames[i].trimmed();
    if (modelKey.isEmpty() || modelName.isEmpty()) {
      continue;
    }

    QString series;
    if (i < availableModelSeries.size()) {
      series = availableModelSeries[i].trimmed();
    }
    if (series.isEmpty()) {
      series = tr("Custom Series");
    }

    modelFileToNameMap.insert(modelKey, modelName);
    modelFileToNameMapProcessed.insert(modelKey, cleanModelName(modelName));
    modelSeriesMap.insert(modelKey, series);

    if (i < releasedDatesParam.size()) {
      const QString released = releasedDatesParam[i].trimmed();
      if (!released.isEmpty()) {
        this->modelReleasedDates.insert(modelKey, released);
      }
    }
  }

  ensureDefaultModelVisible(params, tr("Custom Series"), modelFileToNameMap, modelFileToNameMapProcessed, modelSeriesMap, modelReleasedDates);

  allModelsDownloaded = true;
  for (auto it = modelFileToNameMap.constBegin(); it != modelFileToNameMap.constEnd(); ++it) {
    if (it.value().isEmpty()) {
      continue;
    }
    if (!isModelInstalled(it.key())) {
      allModelsDownloaded = false;
      break;
    }
  }

  QString modelKey = canonicalModelKey(params, QString::fromStdString(params.get("Model")));
  if (modelKey.isEmpty()) {
    modelKey = canonicalModelKey(params, QString::fromStdString(params.get("DrivingModel")));
  }
  if (!isModelInstalled(modelKey)) {
    modelKey = builtinDefaultModelKey(params);
  }
  currentModel = modelFileToNameMap.value(modelKey, builtinDefaultModelName(params));
  selectModelButton->setValue(currentModel);

  noModelsDownloaded = getDeletableModelDisplayNames().isEmpty();

  bool parked = !s.scene.started || fs.starpilot_scene.parked || parent->isFrogsGoMoo;

  deleteModelButton->setEnabled(!(allModelsDownloading || modelDownloading || noModelsDownloaded));

  downloadModelButton->setEnabledButtons(0, !allModelsDownloaded && !allModelsDownloading && !cancellingDownload && fs.starpilot_scene.online && parked);
  downloadModelButton->setEnabledButtons(1, !allModelsDownloaded && !modelDownloading && !cancellingDownload && fs.starpilot_scene.online && parked);

  downloadModelButton->setValue(fs.starpilot_scene.online ? (parked ? "" : "Not parked") : tr("Offline..."));

  started = s.scene.started;

  updateToggles();
}

void StarPilotModelPanel::updateState(const UIState &s, const StarPilotUIState &fs) {
  if (!isVisible() || finalizingDownload) {
    return;
  }

  bool parked = !started || fs.starpilot_scene.parked || parent->isFrogsGoMoo;

  if (allModelsDownloading || modelDownloading) {
    QString progress = QString::fromStdString(params_memory.get("ModelDownloadProgress"));
    bool downloadFailed = progress.contains(QRegularExpression("cancelled|exists|failed|offline", QRegularExpression::CaseInsensitiveOption));

    if (progress != "Downloading...") {
      downloadModelButton->setValue(progress);
    }

    if (progress == "All models downloaded!" && allModelsDownloading || progress == "Downloaded!" && modelDownloading || downloadFailed) {
      finalizingDownload = true;

      QTimer::singleShot(2500, [this, progress]() {
        allModelsDownloaded = progress == "All models downloaded!";
        allModelsDownloading = false;
        cancellingDownload = false;
        finalizingDownload = false;
        modelDownloading = false;
        noModelsDownloaded = false;

        params_memory.remove("CancelModelDownload");
        params_memory.remove("DownloadAllModels");
        params_memory.remove("ModelDownloadProgress");
        params_memory.remove("ModelToDownload");

        downloadModelButton->setEnabled(true);
        downloadModelButton->setValue("");
      });
    }
  } else {
    downloadModelButton->setValue(fs.starpilot_scene.online ? (parked ? "" : "Not parked") : tr("Offline..."));
  }

  deleteModelButton->setEnabled(!(allModelsDownloading || modelDownloading || noModelsDownloaded));

  downloadModelButton->setText(0, modelDownloading ? tr("CANCEL") : tr("DOWNLOAD"));
  downloadModelButton->setText(1, allModelsDownloading ? tr("CANCEL") : tr("DOWNLOAD ALL"));

  downloadModelButton->setEnabledButtons(0, !allModelsDownloaded && !allModelsDownloading && !cancellingDownload && fs.starpilot_scene.online && parked);
  downloadModelButton->setEnabledButtons(1, !allModelsDownloaded && !modelDownloading && !cancellingDownload && fs.starpilot_scene.online && parked);

  downloadModelButton->setVisibleButton(0, !allModelsDownloading);
  downloadModelButton->setVisibleButton(1, !modelDownloading);

  started = s.scene.started;

  parent->keepScreenOn = allModelsDownloading || modelDownloading;
}

void StarPilotModelPanel::updateModelLabels(StarPilotListWidget *labelsList) {
  labelsList->clear();

  QJsonObject modelDrivesAndScores = QJsonDocument::fromJson(QString::fromStdString(params.get("ModelDrivesAndScores")).toUtf8()).object();

  for (const QString &modelName : availableModelNames) {
    QJsonObject modelData = modelDrivesAndScores.value(cleanModelName(modelName)).toObject();

    int drives = modelData.value("Drives").toInt(0);
    int score = modelData.value("Score").toInt(0);

    QString drivesDisplay = drives == 1 ? QString("%1 Drive").arg(drives) : drives > 0 ? QString("%1 Drives").arg(drives) : "N/A";
    QString scoreDisplay = drives > 0 ? QString("Score: %1%").arg(score) : "N/A";

    QString labelTitle = cleanModelName(modelName);
    QString labelText = QString("%1 (%2)").arg(scoreDisplay, drivesDisplay);

    LabelControl *labelControl = new LabelControl(labelTitle, labelText, "", this);
    labelsList->addItem(labelControl);
  }
}

void StarPilotModelPanel::updateToggles() {
  const bool showAllToggles = parent->showAllTogglesEnabled();

  for (auto &[key, toggle] : toggles) {
    bool setVisible = showAllToggles || tuningLevel >= starpilotToggleLevels[key].toDouble();

    if (!showAllToggles) {
      if (key == "ManageBlacklistedModels" || key == "ManageScores") {
        setVisible &= params.getBool("ModelRandomizer");
      } else if (key == "SelectModel") {
        setVisible &= !params.getBool("ModelRandomizer");
      } else if (key == "RecoveryPower") {
        setVisible &= (tuningLevel == 3); // Only visible in developer tuning level
      }
    }

    toggle->setVisible(setVisible);
  }

  update();
}
