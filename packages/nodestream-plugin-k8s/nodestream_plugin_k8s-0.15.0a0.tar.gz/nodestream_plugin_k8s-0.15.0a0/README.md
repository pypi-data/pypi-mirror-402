# Nodestream Kubernetes Plugin 

NOTE: This plugin is still in development and is not ready for production use.

## Overview

This plugin allows you to deploy nodestream on a Kubernete cluster. As your project evolves by adding more data pipelines, `nodstream-plugin-k8s` will be able to manage your kubernetes resources for you. 

## Installation

```bash
pip install nodestream-plugin-k8s
```

## Usage

### 1. Create a `nodestream.yaml` file and project.

```yaml
# nodestream.yaml
scopes:
   crons: 
      pipelines:
        - path: pipelines/crons/my_scheduled_pipeline.yaml
  perpetual:
      pipelines:
        - path: pipelines/perpetual/my_kafka_pipeline.yaml
```

### 2. Annotate your pipeline with `nodestream-plugin-k8s` annotations.

```yaml
# nodestream.yaml
scopes:
   crons:
      pipelines:
        - path: pipelines/crons/my_scheduled_pipeline.yaml
          annotations:
            nodestream_plugin_k8s_schedule: "0 0 * * *"
    perpetual:
       pipelines:
          - path: pipelines/perpetual/my_kafka_pipeline.yaml
            annotations:
              nodestream_plugin_k8s_conccurency: 1
```

### 3. Run `nodestream-plugin-k8s` to deploy your pipelines.

```bash
nodestream k8s sync --namespace my-nodestream-app-namespace 
```


### 4. Check your kubernetes cluster for your deployed pipelines.

```bash
kubectl get cronjobs -n my-nodestream-app-namespace
kubectl get deployments -n my-nodestream-app-namespace
```

### 5. Update your `nodestream.yaml` file and re-run `nodestream-plugin-k8s` to update your pipelines.

```yaml
# nodestream.yaml
scopes:
   crons:
      pipelines:
        - path: pipelines/crons/my_scheduled_pipeline.yaml
          annotations:
            nodestream_plugin_k8s_schedule: "30 0 * * *"
    perpetual:
       pipelines:
          - path: pipelines/perpetual/my_kafka_pipeline.yaml
            annotations:
              nodestream_plugin_k8s_conccurency: 100
```

```bash
nodestream k8s sync --namespace my-nodestream-app-namespace 
```

### 6. Check your kubernetes cluster for your updated pipelines.

```bash
kubectl get cronjobs -n my-nodestream-app-namespace
kubectl get deployments -n my-nodestream-app-namespace
```

### 7. Delete your pipelines.

```bash
nodestream k8s destroy --namespace my-nodestream-app-namespace 
```

## Annotations

### `nodestream_plugin_k8s_schedule`

This annotation is used to schedule a cronjob. The value of this annotation should be a cron expression. 

### `nodestream_plugin_k8s_concurrency`

This annotation is used to set the concurrency of a deployment. The value of this annotation should be an integer.

### `nodestream_plugin_k8s_image`

This annotation is used to set the image of a deployment or job. The value of this annotation should be a valid docker image.
