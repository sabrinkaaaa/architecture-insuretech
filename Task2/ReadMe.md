# Динамическое масштабирование

## Динамическое масштабирование контейнеров

Сервисы InsureTech развернуты в Kubernetes. Каждый из них запущен в определённом количестве экземпляров.
Обычно этого хватает для обработки запросов, но в периоды пиковой нагрузки система начинает вести себя нестабильно: поды перезапускаются из-за нехватки памяти, пользователи сталкиваются с ошибками, и бизнес фиксирует снижение NPS.

Можно было бы держать больше реплик постоянно, но это неэффективно с точки зрения затрат.
Поэтому решаем задачу с помощью **динамического масштабирования** — Kubernetes сам будет увеличивать или уменьшать количество подов в зависимости от нагрузки.


## Тестовое приложение

Для проверки масштабирования используется простое приложение с двумя эндпоинтами:

* `GET /` — возвращает идентификатор пода;
* `GET /metrics` — отдаёт метрики Prometheus, включая `http_requests_total` — количество запросов к приложению.

Приложение работает на порту **8080**.

## Динамическое масштабирование на основании показателей утилизации памяти

1. Поднимите локальный кластер Kubernetes в Minikube:

   ```bash
   minikube start
   ```

2. Активируйте **metrics-server**, который собирает метрики CPU и памяти:

   ```bash
   minikube addons enable metrics-server
   ```

   Дождитесь, пока поды metrics-server будут в статусе **READY 1/1**:

   ```bash
   kubectl get deployment metrics-server -n kube-system
   ```

3. Создайте **Deployment** для тестового приложения.

   * Минимум 1 реплика.
   * Лимит памяти — `30Mi`.
   * Используйте свой собранный образ `scaletestapp:latest`.
     Примените манифест:

   ```bash
   kubectl apply -f scaletest-deployment.yaml
   ```

4. Создайте **Service**, чтобы обращаться к приложению из браузера и Locust:

   ```bash
   kubectl apply -f scaletest-service.yaml
   ```

   Получите URL для тестов:

   ```bash
   minikube service scaletestapp --url
   ```

5. Создайте **Horizontal Pod Autoscaler (HPA)** для масштабирования по памяти.
   Оптимальный уровень утилизации — **80%**, максимум — **10 реплик**.
   Пример манифеста:

   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: scaletestapp-hpa-memory
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: scaletestapp
     minReplicas: 1
     maxReplicas: 10
     metrics:
       - type: Resource
         resource:
           name: memory
           target:
             type: Utilization
             averageUtilization: 80
   ```

   Примените:

   ```bash
   kubectl apply -f hpa-memory.yaml
   ```

6. Проверьте работу автоскейлинга:

   ```bash
   kubectl get hpa -w
   ```

7. Сгенерируйте нагрузку с помощью **Locust**:

   ```bash
   locust
   ```

   Откройте [http://localhost:8089](http://localhost:8089), введите URL сервиса (`minikube service scaletestapp --url`),
   установите количество пользователей (например, 100) и наблюдайте рост реплик в:

   ```bash
   kubectl get pods -l app=scaletestapp
   ```

## Динамическое масштабирование по количеству запросов в секунду (RPS)

Kubernetes по умолчанию масштабирует поды по CPU и памяти,
но в реальных системах часто нужно масштабировать по **RPS** (количество запросов в секунду).
Для этого подключается **Prometheus** и **Prometheus Adapter**, чтобы использовать внешние метрики.


## План работы

1. **Установите Prometheus** через Helm:

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus-operator prometheus-community/kube-prometheus-stack
   ```

2. **Настройте ServiceMonitor** для сбора метрик приложения:

   ```yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: scaletestapp-app-sm
     namespace: default
     labels:
       serviceMonitorSelector: prometheus
   spec:
     endpoints:
       - interval: 10s
         targetPort: 8080
         path: /metrics
     namespaceSelector:
       matchNames:
         - default
     selector:
       matchLabels:
         prometheus-monitored: "true"
   ```

3. **Убедитесь, что Prometheus видит приложение** — в Web UI Prometheus (`Targets`) появится сервис `scaletestapp`.

4. **Настройте Prometheus Adapter** для экспорта кастомной метрики `http_requests_per_second`:

   ```yaml
   prometheus:
     url: "http://<адрес_prometheus>"
   rules:
     default: false
     custom:
       - seriesQuery: 'http_requests_total{namespace!="",pod!=""}'
         resources:
           overrides:
             namespace: {resource: "namespace"}
             pod: {resource: "pod"}
         name:
           matches: "^http_requests_total"
           as: "http_requests_per_second"
         metricsQuery: 'sum(rate(http_requests_total{<<.LabelMatchers>>}[30s])) by (<<.GroupBy>>)'
   ```

   Установите адаптер:

   ```bash
   helm install prometheus-adapter prometheus-community/prometheus-adapter -f values.yaml
   ```

5. **Проверьте наличие метрики:**

   ```bash
   kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1
   ```

6. **Создайте HPA по RPS:**

   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: scaletestapp-hpa-rps
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: scaletestapp
     minReplicas: 1
     maxReplicas: 10
     metrics:
       - type: Pods
         pods:
           metric:
             name: http_requests_per_second
           target:
             type: AverageValue
             averageValue: "5"
   ```

7. **Снова проведите нагрузочное тестирование** через Locust.
   В результате при росте RPS Kubernetes начнёт увеличивать количество подов.


## Для тестирования локально

1. Запустить Minikube:

   ```bash
   minikube start
   ```
2. Применить все манифесты из директории `Task2`:

   ```bash
   kubectl apply -f .
   ```
3. Включить сбор метрик:

   ```bash
   minikube addons enable metrics-server
   ```
4. Запустить Locust:

   ```bash
   locust
   ```
5. Узнать URL сервиса:

   ```bash
   minikube service scaletestapp --url
   ```
6. Подать нагрузку в Locust по этому URL.
7. Смотреть автоскейлинг в реальном времени:

   ```bash
   kubectl get hpa -w
   ```
8. Открыть дашборд:

   ```bash
   minikube dashboard
   ```
9. Просмотреть события:

   ```bash
   kubectl describe deployment scaletestapp
   ```

