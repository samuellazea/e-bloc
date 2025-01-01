import logging
import aiofiles
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from aiohttp import ClientSession
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceEntryType

from .const import (
    DOMAIN,
    URL_LOGIN,
    HEADERS_LOGIN,
    HEADERS_POST,
    URL_HOME,
    URL_INDEX,
    URL_RECEIPTS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)
luna_afisata = None

class EBlocDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordonator pentru actualizarea datelor în integrarea E-bloc."""

    def __init__(self, hass, config):
        """Inițializare coordonator."""
        super().__init__(
            hass,
            _LOGGER,
            name="EBlocDataUpdateCoordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.hass = hass
        self.config = config
        self.session = None
        self.authenticated = False

    async def _async_update_data(self):
        """Actualizează datele pentru toate componentele."""
        try:
            if not self.session:
                self.session = ClientSession()
            if not self.authenticated:
                await self._authenticate()

            today = datetime.now()
            # Calculate the first day of the current month
            first_day_of_current_month = today.replace(day=1)

            # Calculate the last day of the previous month by subtracting one day from the first day of the current month
            #last_day_of_previous_month = first_day_of_current_month -  timedelta(days=1)
            last_day_of_previous_month = first_day_of_current_month -  relativedelta(months=2)

            # Get the previous month and year
            previous_year = last_day_of_previous_month.year
            previous_month = last_day_of_previous_month.month
            
            # return {
            #     "home": await self._fetch_data(URL_HOME, {"pIdAsoc": self.config["pIdAsoc"], "pIdAp": self.config["pIdAp"]}),
            #     "index": await self._fetch_data(URL_INDEX, {"pIdAsoc": self.config["pIdAsoc"], "pLuna": "2024-12", "pIdAp": self.config["pIdAp"]}),
            #     "receipts": await self._fetch_data(URL_RECEIPTS, {"pIdAsoc": self.config["pIdAsoc"], "pIdAp": self.config["pIdAp"]}),
            # }            

            payload = {
                "pIdAsoc": self.config["pIdAsoc"],
                "pIdAp": self.config["pIdAp"],
                "pLuna": f"{previous_year}-{previous_month:02d}"
            }
            _LOGGER.debug("Payload for data fetch: %s", payload)

            return {
                "home": await self._fetch_data(URL_HOME, payload),
                "index": await self._fetch_data(URL_INDEX, payload),
                "receipts": await self._fetch_data(URL_RECEIPTS, payload),
            }
        except Exception as e:
            raise UpdateFailed(f"Eroare la actualizarea datelor: {e}")

    async def _authenticate(self):
        """Autentificare pe server."""
        payload = {"pUser": self.config["pUser"], "pPass": self.config["pPass"]}
        try:
            async with self.session.post(URL_LOGIN, data=payload, headers=HEADERS_LOGIN) as response:
                if response.status == 200 and "Acces online proprietari" in await response.text():
                    _LOGGER.debug("Autentificare reușită.")
                    self.authenticated = True
                else:
                    raise UpdateFailed("Autentificare eșuată.")
        except Exception as e:
            raise UpdateFailed(f"Eroare la autentificare: {e}")

    async def _fetch_data(self, url, payload):
        """Execută cererea POST și returnează răspunsul JSON."""
        try:
            async with self.session.post(url, data=payload, headers=HEADERS_POST) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    _LOGGER.error("Eroare la accesarea %s: Status %s", url, response.status)
                    return {}
        except Exception as e:
            _LOGGER.error("Eroare la conexiunea cu serverul: %s", e)
            return {}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setăm senzorii pentru integrarea E-bloc."""
    coordinator = EBlocDataUpdateCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        EBlocHomeSensor(coordinator),
        EBlocContoareSensorApaRece(coordinator),
        EBlocContoareSensorApaCalda(coordinator),
        EBlocContoareSensorCaldura(coordinator),
        EBlocContoareSensorCurent(coordinator),
        EBlocPlatiChitanteSensor(coordinator),
    ]
    async_add_entities(sensors, update_before_add=True)


class EBlocSensorBase(SensorEntity):
    """Clasă de bază pentru senzorii E-bloc."""

    def __init__(self, coordinator, name):
        self._coordinator = coordinator
        self._attr_name = name
        self._attr_state = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        """Actualizează datele pentru senzor."""
        await self._coordinator.async_request_refresh()


class EBlocHomeSensor(EBlocSensorBase):
    """Senzor pentru `AjaxGetHomeApInfo.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Date client")

    async def async_update(self):
        """Actualizează datele pentru senzorul `home`."""
        data = self._coordinator.data.get("home", {}).get("1", {})
        
        # Update the global variable luna_afisata
        global luna_afisata
        luna_afisata = data.get("luna_afisata", "Necunoscut")

        # Log the updated luna_afisata
        _LOGGER.debug("Updated luna_afisata: %s", luna_afisata)
        
        self._attr_state = data.get("cod_client", "Necunoscut")
        self._attr_extra_state_attributes = {
            "Cod client": data.get("cod_client", "Necunoscut"),
            "Apartament": data.get("ap", "Necunoscut"),
            "Persoane declarate": data.get("nr_pers_afisat", "Necunoscut"),
            "Restanță de plată": f"{int(data.get('datorie', 0)) / 100:.2f} RON"
            if data.get("datorie") != "Necunoscut"
            else "Necunoscut",
            "Ultima zi de plată": data.get("ultima_zi_plata", "Necunoscut"),
            "Contor trimis": "Da"
            if data.get("contoare_citite", "Necunoscut") == "1"
            else "Nu",
            "Începere citire contoare": data.get("citire_contoare_start", "Necunoscut"),
            "Încheiere citire contoare": data.get("citire_contoare_end", "Necunoscut"),
            "Luna cu datoria cea mai veche": data.get("luna_veche", "Necunoscut"),
            "Luna afișată": data.get("luna_afisata", "Necunoscut"),
            "Nivel restanță": data.get("nivel_restanta", "Necunoscut"),
        }

    @property
    def unique_id(self):
        return f"{DOMAIN}_client"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:account-file"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }

class EBlocContoareSensorApaRece(EBlocSensorBase):
    """Senzor pentru `AjaxGetIndexContoare.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Index contor Apa Rece")

    async def async_update(self):
        
        # Log the entire coordinator data
        _LOGGER.debug("Full coordinator data: %s", self._coordinator.data)
        
        """Actualizează datele pentru senzorul `index`."""
        data = self._coordinator.data.get("index", {}).get("2", {})
        
        # Log the retrieved data for this specific sensor
        _LOGGER.debug("Fetched data for Index contor Apa Rece: %s", data)
        
        index_vechi = data.get("index_vechi", "").strip()
        index_nou = data.get("index_nou", "").strip()

        try:
            index_vechi = f"{float(index_vechi) / 1000:.3f}" if index_vechi else "Necunoscut"
        except ValueError:
            index_vechi = "Necunoscut"

        try:
            index_nou = f"{float(index_nou) / 1000:.3f}" if index_nou else "Necunoscut"
        except ValueError:
            index_nou = "Necunoscut"

        # Setăm starea senzorului pentru `index_nou`
        self._attr_state = (
            f"{index_nou}" if index_nou != "Necunoscut" else "Necunoscut"
        )

        # Atribute suplimentare
        self._attr_extra_state_attributes = {
            "Index vechi": f"{index_vechi}"
            if index_vechi != "Necunoscut"
            else "Necunoscut",
            "Index nou": f"{index_nou}"
            if index_nou != "Necunoscut"
            else "",
            "Luna afisata": luna_afisata
            if luna_afisata != "Necunoscut"
            else "Necunoscut",
            "Unitate masurare": "mc",
        }

    @property
    def unique_id(self):
        return f"{DOMAIN}_contor_apa_rece"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:counter"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }

class EBlocContoareSensorApaCalda(EBlocSensorBase):
    """Senzor pentru `AjaxGetIndexContoare.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Index contor Apa Calda")

        data = self._coordinator.data.get("index", {}).get("3", {})
        index_vechi = data.get("index_vechi", "").strip()
        index_nou = data.get("index_nou", "").strip()

        try:
            index_vechi = f"{float(index_vechi) / 1000:.3f}" if index_vechi else "Necunoscut"
        except ValueError:
            index_vechi = "Necunoscut"

        try:
            index_nou = f"{float(index_nou) / 1000:.3f}" if index_nou else "Necunoscut"
        except ValueError:
            index_nou = "Necunoscut"

        # Setăm starea senzorului pentru `index_nou`
        self._attr_state = (
            f"{index_nou}" if index_nou != "Necunoscut" else "Necunoscut"
        )

        # Atribute suplimentare
        self._attr_extra_state_attributes = {
            "Index vechi": f"{index_vechi}"
            if index_vechi != "Necunoscut"
            else "Necunoscut",
            "Index nou": f"{index_nou}"
            if index_nou != "Necunoscut"
            else "",
            "Luna afisata": luna_afisata
            if luna_afisata != "Necunoscut"
            else "Necunoscut",            
            "Unitate masurare": "mc",
        }
        
    @property
    def unique_id(self):
        return f"{DOMAIN}_contor_apa_calda"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:counter"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }
        
class EBlocContoareSensorCaldura(EBlocSensorBase):
    """Senzor pentru `AjaxGetIndexContoare.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Index contor Caldura")

        data = self._coordinator.data.get("index", {}).get("4", {})
        index_vechi = data.get("index_vechi", "").strip()
        index_nou = data.get("index_nou", "").strip()

        try:
            index_vechi = f"{float(index_vechi) / 1000:.3f}" if index_vechi else "Necunoscut"
        except ValueError:
            index_vechi = "Necunoscut"

        try:
            index_nou = f"{float(index_nou) / 1000:.3f}" if index_nou else "Necunoscut"
        except ValueError:
            index_nou = "Necunoscut"

        # Setăm starea senzorului pentru `index_nou`
        self._attr_state = (
            f"{index_nou}" if index_nou != "Necunoscut" else "Necunoscut"
        )

        # Atribute suplimentare
        self._attr_extra_state_attributes = {
            "Index vechi": f"{index_vechi}"
            if index_vechi != "Necunoscut"
            else "Necunoscut",
            "Index nou": f"{index_nou}"
            if index_nou != "Necunoscut"
            else "",
            "Luna afisata": luna_afisata
            if luna_afisata != "Necunoscut"
            else "Necunoscut",            
            "Unitate masurare": "mc",
        }
        
    @property
    def unique_id(self):
        return f"{DOMAIN}_contor_caldura"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:counter"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }

class EBlocContoareSensorCurent(EBlocSensorBase):
    """Senzor pentru `AjaxGetIndexContoare.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Index contor Curent")

        data = self._coordinator.data.get("index", {}).get("5", {})
        index_vechi = data.get("index_vechi", "").strip()
        index_nou = data.get("index_nou", "").strip()

        try:
            index_vechi = f"{float(index_vechi) / 1000:.3f}" if index_vechi else "Necunoscut"
        except ValueError:
            index_vechi = "Necunoscut"

        try:
            index_nou = f"{float(index_nou) / 1000:.3f}" if index_nou else "Necunoscut"
        except ValueError:
            index_nou = "Necunoscut"

        # Setăm starea senzorului pentru `index_nou`
        self._attr_state = (
            f"{index_nou}" if index_nou != "Necunoscut" else "Necunoscut"
        )

        # Atribute suplimentare
        self._attr_extra_state_attributes = {
            "Index vechi": f"{index_vechi}"
            if index_vechi != "Necunoscut"
            else "Necunoscut",
            "Index nou": f"{index_nou}"
            if index_nou != "Necunoscut"
            else "",
            "Luna afisata": luna_afisata
            if luna_afisata != "Necunoscut"
            else "Necunoscut",
            "Unitate masurare": "kWh",
        }
        
    @property
    def unique_id(self):
        return f"{DOMAIN}_contor_curent"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:counter"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }
        
class EBlocPlatiChitanteSensor(EBlocSensorBase):
    """Senzor pentru `AjaxGetPlatiChitanteToti.php`."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Plăți și chitanțe")

    async def async_update(self):
        """Actualizează datele pentru senzorul `plati_chitante`."""
        data = self._coordinator.data.get("receipts", {})
        numar_chitante = len(data)

        # Setăm starea senzorului pe baza numărului de chitanțe
        self._attr_state = numar_chitante

        # Creăm atribute suplimentare
        atribute = {"Număr total de chitanțe": numar_chitante}
        for idx, chitanta_data in data.items():
            numar = chitanta_data.get("numar", "Necunoscut")
            data_chitanta = chitanta_data.get("data", "Necunoscut")
            suma = chitanta_data.get("suma", "0")
            suma_formatata = f"{int(suma) / 100:.2f} RON"

            # Formatul exact al atributelor (fără "Chitanță X")
            atribute[f"Chitanță {idx}"] = numar
            atribute[f"Data {idx}"] = data_chitanta
            atribute[f"Sumă plătită {idx}"] = suma_formatata

        # Atribuim atributele suplimentare
        self._attr_extra_state_attributes = atribute

    @property
    def unique_id(self):
        return f"{DOMAIN}_plati_si_chitante"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def icon(self):
        """Pictograma senzorului."""
        return "mdi:credit-card-check-outline"

    @property
    def device_info(self):
        """Returnează informațiile dispozitivului."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Interfață UI pentru E-bloc.ro",
            "manufacturer": "E-bloc.ro",
            "model": "Interfață UI pentru E-bloc.ro",
            "entry_type": DeviceEntryType.SERVICE,
        }
