#include <Arduino.h>
SemaphoreHandle_t xMutex;
void HandleSerial(const char *text)
{
    if (xSemaphoreTake(xMutex, portMAX_DELAY))
    {
        Serial.println(text);
        xSemaphoreGive(xMutex);
    }
}

void TaskA(void *pvParameters)
{
    while (1)
    {
        HandleSerial("Task A: Hello from Task A!");
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }
}
void TaskB(void *pvParameters)
{
    while (1)
    {
        HandleSerial("Task B: Greetings from Task B!");
        vTaskDelay(700 / portTICK_PERIOD_MS);
    }
}
void TaskC(void *pvParameters)
{
    while (1)
    {
        HandleSerial(R"(===== Task C Start =====
line 1
line 2
===== Task C End =====)");
        vTaskDelay(700 / portTICK_PERIOD_MS);
    }
}
void setup()
{
    Serial.begin(9600);
    xMutex = xSemaphoreCreateMutex();
    xTaskCreate(TaskA, "TaskA", 2048, NULL, 1, NULL);
    xTaskCreate(TaskB, "TaskB", 2048, NULL, 1, NULL);
    xTaskCreate(TaskC, "TaskC", 2048, NULL, 2, NULL);
}
void loop() {}
