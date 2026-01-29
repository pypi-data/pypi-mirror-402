# Changelog

## [0.3.0](https://github.com/kubeflow/sdk/releases/tag/0.3.0) (2026-01-16)

### 🚀 Features

- feat: updated release.yml and rm prev script (Akash Jaiswal)
- feat: added git cliff for changelogs (Akash Jaiswal)
- feat(docs): KEP- Spark Client for Kubeflow SDK ([#163](https://github.com/kubeflow/sdk/pull/163) by @Shekharrajak)
- feat(trainer): add get_job_events API to retrieve TrainJob events ([#220](https://github.com/kubeflow/sdk/pull/220) by @sksingh2005)
- feat(trainer): support NVIDIA MIG device resources in TrainJob device… ([#204](https://github.com/kubeflow/sdk/pull/204) by @LabsJS)
- feat: Add custom instructions for GitHub Copilot ([#212](https://github.com/kubeflow/sdk/pull/212) by @osamaahmed17)
- feat:  Add callbacks to the wait_for_job_status() API ([#205](https://github.com/kubeflow/sdk/pull/205) by @osamaahmed17)
- feat(trainer): Allow to reference runtime by name ([#214](https://github.com/kubeflow/sdk/pull/214) by @andreyvelich)
- feat(trainer): Support optional image for CustomTrainer ([#216](https://github.com/kubeflow/sdk/pull/216) by @andreyvelich)
- feat: Add dependabot to Kubeflow SDK ([#194](https://github.com/kubeflow/sdk/pull/194) by @kramaranya)
- feat(docs): Update README with announcement blog post ([#157](https://github.com/kubeflow/sdk/pull/157) by @andreyvelich)


### 🐛 Bug Fixes

- fix: default changelog script (Akash Jaiswal)
- fix: version (Akash Jaiswal)
- fix: project toml (Akash Jaiswal)
- fix: release on forks (Akash Jaiswal)
- fix: config, script and revert local tag release (Akash Jaiswal)
- fix: update the format with title (#PR by @username) (Akash Jaiswal)
- fix: use full version name, rm test falgs and edited config to take full PR name (Akash Jaiswal)
- fix: detect prev version automatically and updated release.md (Akash Jaiswal)
- fix: Upgrade urllib3 to  v2.6.1 ([#193](https://github.com/kubeflow/sdk/pull/193) by @Fiona-Waters)
- fix(trainer): expose CustomTrainerContainer for import ([#185](https://github.com/kubeflow/sdk/pull/185) by @AndEsterson)
- fix: update permissions for welcome workflow to avoid 403 error ([#181](https://github.com/kubeflow/sdk/pull/181) by @aniketpati1121)
- fix(ci): Move permissions to the workflow root ([#177](https://github.com/kubeflow/sdk/pull/177) by @kramaranya)
- fix: pip install with --user argument fails with image running in python virtual environment ([#162](https://github.com/kubeflow/sdk/pull/162) by @briangallagher)
- fix(trainer): Remove namespace from ClusterTrainingRuntime exception messages ([#166](https://github.com/kubeflow/sdk/pull/166) by @astefanutti)
- fix(trainer): Use PyTorch static rendezvous in container backend ([#168](https://github.com/kubeflow/sdk/pull/168) by @astefanutti)
- fix(trainer): Fix listing containers with Podman backend ([#154](https://github.com/kubeflow/sdk/pull/154) by @astefanutti)


### 💼 Other

- Kubeflow SDK Official Release 0.2.1 ([#180](https://github.com/kubeflow/sdk/pull/180) by @kramaranya)


### ⚙️ Miscellaneous Tasks

- chore: rm v pattern (Akash Jaiswal)
- chore: format issue and fix feature title (Akash Jaiswal)
- chore: reverter rename of script (Akash Jaiswal)
- chore: refactor the script into different file and fixing the release yml (Akash Jaiswal)
- chore: Nominate @kramaranya as Kubeflow SDK approver ([#206](https://github.com/kubeflow/sdk/pull/206) by @andreyvelich)
- chore(ci): bump softprops/action-gh-release from 1 to 2 ([#209](https://github.com/kubeflow/sdk/pull/209) by @dependabot[bot])
- chore(ci): bump actions/upload-artifact from 4 to 6 ([#208](https://github.com/kubeflow/sdk/pull/208) by @dependabot[bot])
- chore(ci): bump actions/download-artifact from 6 to 7 ([#207](https://github.com/kubeflow/sdk/pull/207) by @dependabot[bot])
- chore(ci): bump amannn/action-semantic-pull-request from 5.5.3 to 6.1.1 ([#210](https://github.com/kubeflow/sdk/pull/210) by @dependabot[bot])
- chore(ci): bump actions/github-script from 7 to 8 ([#201](https://github.com/kubeflow/sdk/pull/201) by @dependabot[bot])
- chore(ci): bump actions/download-artifact from 4 to 6 ([#200](https://github.com/kubeflow/sdk/pull/200) by @dependabot[bot])
- chore(ci): bump actions/stale from 5 to 10 ([#199](https://github.com/kubeflow/sdk/pull/199) by @dependabot[bot])
- chore(ci): bump actions/setup-python from 5 to 6 ([#198](https://github.com/kubeflow/sdk/pull/198) by @dependabot[bot])
- chore(ci): bump actions/checkout from 4 to 6 ([#202](https://github.com/kubeflow/sdk/pull/202) by @dependabot[bot])
- chore(docs): Add new items to the roadmap ([#187](https://github.com/kubeflow/sdk/pull/187) by @kramaranya)


### 🎉 New Contributors
- @Shekharrajak — welcome and thanks for your first contribution!
- @sksingh2005 — welcome and thanks for your first contribution!
- @LabsJS — welcome and thanks for your first contribution!
- @osamaahmed17 — welcome and thanks for your first contribution!
- @andreyvelich — welcome and thanks for your first contribution!
- @dependabot[bot] — welcome and thanks for your first contribution!
- @kramaranya — welcome and thanks for your first contribution!
- @Fiona-Waters — welcome and thanks for your first contribution!
- @AndEsterson — welcome and thanks for your first contribution!
- @aniketpati1121 — welcome and thanks for your first contribution!
- @briangallagher — welcome and thanks for your first contribution!
- @astefanutti — welcome and thanks for your first contribution!
