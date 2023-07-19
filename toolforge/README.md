Everything in this directory is related to running ISA on [Toolforge](https://www.toolforge.org/). If you're running it anywhere else the content is not relevant or at least needs to be adapted.

## Content

* deploy.sh - Deploys ISA step by step.
* start-celery.sh - Starts Celery worker.

## Config

Add the following values to the config:

```
CELERY:
    broker_url: redis://redis.svc.tools.eqiad1.wikimedia.cloud
    task_default_queue: # Long random string, see https://wikitech.wikimedia.org/wiki/Help:Toolforge/Redis_for_Toolforge#Celery
```
