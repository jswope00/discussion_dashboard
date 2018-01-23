# Discussion Dashboard X-block
A dashboard to show discussion activities within Open EdX

Installation
------------

Make sure that `ALLOW_ALL_ADVANCED_COMPONENTS` feature flag is set to `True` in `cms.env.json`.

Change user and activate env:

```bash
sudo -H -u edxapp bash
source /edx/app/edxapp/edxapp_env
```

Get the source to the /edx/app/edxapp/ folder:

```bash
cd /edx/app/edxapp/
git clone https://github.com/jswope00/discussion_dashboard.git
```

For Installation:
```bash
pip install discussion_dashboard/
```

To upgrade an existing installation of this XBlock, fetch the latest code and then update:

```bash
cd discussion_dashboard/
git pull origin master
cd ..
pip install -U --no-deps discussion_dashboard/
```

Restart Edxapp:

```bash
exit
sudo /edx/bin/supervisorctl restart edxapp:
```

Enabling in Studio
------------------

You can enable the discussion_dashboard in studio through the advanced
settings.

1. From the main page of a specific course, navigate to `Settings ->
   Advanced Settings` from the top menu.
2. Check for the `advanced_modules` policy key, and add
   `"discussion_dashboard"` to the policy value list.
3. Click the "Save changes" button.
