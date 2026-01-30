# aind_watchdog_service

## Usage

Watchdog runs in the background (see [deployment](#deployment)), and watches a directory for newly-created yaml files containing instructions to transfer files.

On a computer where the watchdog service is running, manifests can be submitted by creating a file in the right folder. To do this in your software, `pip install aind-watchdog-service` and use the `aind_watchdog_service.models.ManifestConfig` object to write your manifest file in the proper format. See the examples/ folder in this repo for more details.

## Configuration

Watchdog is configured using SIPE's configuration zookeeper server. The configuration options are listed in /src/aind_watchdog_service/models/watch_config.py.

## Monitoring

Watchdog logs can be monitored from the main SIPE logserver (http://eng-logtools:8080/?channel_filter=watchdog&hide=location,count) or this [grafana dashboard](http://eng-tools/grafana/d/de377sfsa9fcwf/watchdog-service-logs?var-acquisition_age=7d&orgId=2&from=now-7d&to=now&timezone=browser&var-hostname=$__all&refresh=auto).

## Deployment

Deployment in the institute is handled by SIPE systems engineers, submit a [SIPE Request](https://apps.powerapps.com/play/e/9084dabc-d707-e1bf-8113-685be25cac15/a/cb338490-e23d-48e6-9e6d-e600b8d17dd4?tenantId=32669cd6-737f-4b39-8bdd-d6951120d3fc&hidenavbar=true) if you need watchdog installed somewhere.

Github actions are used to compile aind-watchdog-service into an executable using pyinstaller. This executable is attached to a Github Release and uploaded to SIPE's software /releases storage, where it can be deployed to rigs in the institute.

Watchdog should be deployed on a SIPE-accessible rig via the install-aind_watchdog_service.yml ansible script. This will download the app and set up a windows scheduled task to run the service. By default, the scheduled task includes a nightly restart at 11:30pm. If the task is running, the scheduler will kill the old instance and start the new one - due to how task scheduler force kills processes, the death of an old process will not generate a stop log.

## Testing
Watchdog has a bundled test function that will create some dummy data on the rig and create a manifest file to transfer that data. Once  Run it with the below commands:

```
cd "C://Program Files/AIBS_MPE/aind_watchdog_service"
aind_watchdog_service.exe --test
```

It will print something like the following:
```
Data created at C:\ProgramData\AIBS_MPE\aind_watchdog_service\logs\test_data
Manifest created at C:\Users\svc_mpe\Documents\aind_watchdog_service\manifest\test_manifest_2024-11-15_17-31-25.yml
```

Make sure that the running instance of watchdog picks up the manifest and completes the transfer.

## Development

Clone the repo
Install dependencies with `uv sync --extra service --extra dev`
Run the service with `uv run src/aind_watchdog_service/main.py`

(If not using uv, use `pip install .[service]` and `python src/aind_watchdog_service/main.py`)
