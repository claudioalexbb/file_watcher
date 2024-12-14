This script will upload to discord (or other URLs that accept JSON bodies) the contents of the files designated in the config file.

The configuration file ("file_watcher_config.json") should follow the following structure:
```
[
    {
        "baseFilename" : "*myLog*",
        "filePath" : "Logs/",
        "canHaveMultipleFiles" : true,
        "keywords" :
        {
            "include" : [],
            "exclude" : []
        },
        "channel_webhook" : "https://discord.com/api/webhooks/XYZ"
    },
    {
        "baseFilename" : "System*.log",
        "filePath" : "Logs/",
        "canHaveMultipleFiles" : false,
        "keywords" :
        {
            "include" : [],
            "exclude" : ["exclude this","also excluded"]
        },
        "channel_webhook" : "https://discord.com/api/webhooks/ABC"
    }
]
```

- baseFilename + filePath: define the path and filename search pattern. If there are multiple files that fit the pattern, the script will choose the most recent file.
- canHaveMultipleFiles: usually when logs reach a certain size, systems create a new file with a new date. if that is your case, you can set this to "true" and the script will automatically search for new files
- keywords: you can choose to only upload certain lines instead of the full content of the files.
In those cases, you can use the exclude and include to:
  - exclude: if not empty, only lines NOT matching the keywords will be uploaded
  - include: if not empty, only lines MATCHING the keywords will be uploaded.
    Note: exclude has priority meaning that if a line is excluded by the exclude, it wont be uplaoded even if it matchs the include keyword.
- channel_webhook: discord webhook url. to create one, go to a channel, click on channel settings - integration - webhooks.

You can set individual URLs for each file and even repeat the same file with different configurations.