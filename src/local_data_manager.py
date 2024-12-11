import json
import os


class LocalDataManager:
    def __init__(self, base_path="data"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self.ensure_files_exist()

    def ensure_files_exist(self):
        """Создает JSON-файлы, если их нет."""
        transport_companies_path = os.path.join(self.base_path, "transport_companies.json")
        destinations_path = os.path.join(self.base_path, "destinations.json")

        if not os.path.exists(transport_companies_path):
            with open(transport_companies_path, "w") as f:
                json.dump({"transport_companies": ["DHL", "DHL ECO", "UPS", "TNT", "BRING"]}, f)

        if not os.path.exists(destinations_path):
            with open(destinations_path, "w") as f:
                json.dump({"destinations": ["KKN", "TXM", "KGD", "MMK"]}, f)

    def load_transport_companies(self):
        """Загружает список транспортных компаний."""
        try:
            with open(os.path.join(self.base_path, "transport_companies.json"), "r") as f:
                data = json.load(f)
            return data.get("transport_companies", [])
        except Exception as e:
            print(f"Error loading transport companies: {e}")
            return []

    def load_destinations(self):
        """Загружает список пунктов назначения."""
        try:
            with open(os.path.join(self.base_path, "destinations.json"), "r") as f:
                data = json.load(f)
            return data.get("destinations", [])
        except Exception as e:
            print(f"Error loading destinations: {e}")
            return []
