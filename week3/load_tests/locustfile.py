from locust import HttpUser, task, between


class IRCTCUser(HttpUser):
    # Simulate users waiting between requests
    wait_time = between(1, 2)

    @task(9)
    def check_availability(self):
        self.client.get("/availability")

    @task(1)
    def check_health(self):
        self.client.get("/health")