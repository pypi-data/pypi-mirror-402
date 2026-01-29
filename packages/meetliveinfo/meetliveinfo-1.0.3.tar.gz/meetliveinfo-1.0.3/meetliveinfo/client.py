from __future__ import annotations

from typing import Any, Optional
import requests

from meetliveinfo.models.agegroup import AgeGroupsResponse
from meetliveinfo.models.athlete import Athlete, AthletesResponse
from meetliveinfo.models.club import Club, ClubsResponse
from meetliveinfo.models.entries import EntriesResponse
from meetliveinfo.models.events import EventsResponse
from meetliveinfo.models.events_by_session import EventsBySessionResponse
from meetliveinfo.models.events_by_stroke import EventsByStrokeResponse
from meetliveinfo.models.globals import GlobalsResponse
from meetliveinfo.models.heat import HeatResultResponse
from meetliveinfo.models.medals import MedalsResponse
from meetliveinfo.models.pointscores import PointScore, PointScoreDetailsResponse, PointScoresResponse
from meetliveinfo.models.record_by_event import RecordByEventItem, RecordsByEventResponse
from meetliveinfo.models.records import RecordItem, RecordListResponse, RecordsResponse
from meetliveinfo.models.results import ResultsResponse


class HTTPClient:
    """
    HTTP client для Splash Meet Manager Live Info Server.

    Этот клиент предоставляет методы для работы с API Live Info Server, встроенного
    в Meet Manager. Он поддерживает получение информации о спортсменах, клубах,
    событиях, результатах, медалях, рекордах и очках.

    Параметры:
        base_url (str): Базовый URL сервера (по умолчанию "http://localhost:3001").
        timeout (float): Время ожидания HTTP-запроса в секундах (по умолчанию 5.0).
        language (Optional[str]): Язык ответа от сервера. Можно указать "us" для английского.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        timeout: float = 5.0,
        language: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.language = language

    # =========================
    # Internal helpers
    # =========================

    def _get_json(self, path: str, params: dict | None = None) -> Any:
        """
        Выполняет GET-запрос к серверу и возвращает данные в формате JSON.

        Args:
            path (str): Путь API (например, "/athletes").
            params (dict | None): Дополнительные параметры запроса.

        Returns:
            Any: Декодированные JSON-данные.
        """
        params = params or {}

        if self.language and "language" not in params:
            params["language"] = self.language

        resp = requests.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # =========================
    # Static lists
    # =========================

    def get_agegroups(self) -> AgeGroupsResponse:
        """
        Получает список всех возрастных групп.

        Returns:
            AgeGroupsResponse: Модель с информацией о возрастных группах,
            включающая buildnr, lastupdate и список agegroups.

        Example:
            >>> client = HTTPClient()
            >>> agegroups = client.get_agegroups()
            >>> print(agegroups.agegroups)
        """
        data: dict = self._get_json("/agegroups")
        buildnr = data.pop("buildnr")
        lastupdate = data.pop("lastupdate")
        agegroups = data.values()
        normalized = {
            "buildnr": buildnr,
            "lastupdate": lastupdate,
            "agegroups": agegroups,
        }
        return AgeGroupsResponse.model_validate(normalized)

    def get_athletes(self) -> AthletesResponse:
        """
        Получает список всех спортсменов.

        Returns:
            AthletesResponse: Список моделей Athlete.

        Example:
            >>> athletes = client.get_athletes()
            >>> print(athletes[0].name)
        """
        data: list = self._get_json("/athletes")
        return [Athlete.model_validate(d) for d in data]

    def get_clubs(self) -> ClubsResponse:
        """
        Получает список всех клубов.

        Returns:
            ClubsResponse: Список моделей Club.
        """
        data: list = self._get_json("/clubs")
        return [Club.model_validate(d) for d in data]

    def get_globals(self) -> GlobalsResponse:
        """
        Получает общую информацию о соревновании.

        Returns:
            GlobalsResponse: Модель с информацией о текущем соревновании,
            сессиях и других глобальных настройках.
        """
        data: dict = self._get_json("/globals")
        return GlobalsResponse.model_validate(data)

    # =========================
    # Events
    # =========================

    def get_events(self) -> EventsResponse:
        """
        Получает список всех событий (дисциплин) соревнования.

        Returns:
            EventsResponse: Модель с buildnr, lastupdate и списком events.
        """
        data: dict = self._get_json("/events")
        buildnr = data.pop("buildnr")
        lastupdate = data.pop("lastupdate")
        events = data.values()
        normalized = {
            "buildnr": buildnr,
            "lastupdate": lastupdate,
            "events": events,
        }
        return EventsResponse.model_validate(normalized)

    def get_events_by_session(self) -> EventsBySessionResponse:
        """
        Получает события, сгруппированные по сессиям.

        Returns:
            EventsBySessionResponse: Модель с событиями по сессиям,
            содержащая только id и статус события.
        """
        data = self._get_json("/events/bysession")
        return EventsBySessionResponse.model_validate(data)

    def get_events_by_stroke(self) -> EventsByStrokeResponse:
        """
        Получает события, сгруппированные по стилям плавания и полу.

        Returns:
            EventsByStrokeResponse: Модель с событиями по стилям и полу,
            содержащая только id и статус события.
        """
        data: dict = self._get_json("/events/bystroke")
        return EventsByStrokeResponse.model_validate(data)

    # =========================
    # Entries
    # =========================

    def get_entries_for_event(self, event: int) -> EntriesResponse:
        """
        Получает список всех заявок на конкретное событие.

        Args:
            event (int | str): Номер или код события (например, 23 или "20F").

        Returns:
            EntriesResponse: Модель с информацией о заявках на событие.
        """
        data: dict = self._get_json(f"/entries/{event}")
        return EntriesResponse.model_validate(data)

    # =========================
    # Heats
    # =========================

    def get_heat(self, event: int, heat: int) -> HeatResultResponse:
        """
        Получает информацию о конкретном заплыве.

        Args:
            event (int | str): Номер или код события.
            heat (int): Номер заплыва.

        Returns:
            HeatResultResponse: Модель с участниками и результатами заплыва.
        """
        data: dict = self._get_json(f"/heats/{event}/{heat}")
        return HeatResultResponse.model_validate(data)

    def get_heat_by_id(self, heat_id: int) -> HeatResultResponse:
        """
        Получает информацию о заплыве по уникальному идентификатору.

        Args:
            heat_id (int): Уникальный ID заплыва.

        Returns:
            HeatResultResponse: Модель с участниками и результатами заплыва.
        """
        data: dict = self._get_json(f"/heats/byid/{heat_id}")
        return HeatResultResponse.model_validate(data)

    def get_ares_heat(
        self,
        event: int,
        round_code: int,
        heat: int,
    ) -> dict[str, Any]:
        """
        Получает данные заплыва в формате системы тайминга Ares.

        Args:
            event (int | str): Номер или код события.
            round_code (int): Код раунда (1=Timed Final, 2=Prelims и т.д.).
            heat (int): Номер заплыва.

        Returns:
            dict[str, Any]: Сырой JSON-ответ Ares с результатами заплыва.
        """
        data: dict = self._get_json(f"/heats/ares/{event}/{round_code}/{heat}")
        return data

    # =========================
    # Results
    # =========================

    def get_results_for_event(self, event: int) -> ResultsResponse:
        """
        Получает результаты конкретного события.

        Args:
            event (int | str): Номер или код события.

        Returns:
            ResultsResponse: Модель с результатами по возрастным группам.
        """
        data: dict = self._get_json(f"/results/{event}")
        return ResultsResponse.model_validate(data)

    # =========================
    # Medals
    # =========================

    def get_medal_statistics(self) -> MedalsResponse:
        """
        Получает текущую статистику медалей.

        Returns:
            MedalsResponse: Модель с количеством медалей по клубам и спортсменам.
        """
        data: dict = self._get_json("/medals")
        return MedalsResponse.model_validate(data)

    def get_medals_for_event(self, event: str | int) -> ResultsResponse:
        """
        Получает список медалистов конкретного события.

        Args:
            event (int | str): Номер или код события.

        Returns:
            ResultsResponse: Модель с результатами и медалями для события.
        """
        data: dict = self._get_json(f"/medals/{event}")
        return ResultsResponse.model_validate(data)

    # =========================
    # Point scores
    # =========================

    def get_point_scores(self) -> PointScoresResponse:
        """
        Получает список всех определений очков соревнования.

        Returns:
            PointScoresResponse: Список моделей PointScore.
        """
        data: list = self._get_json("/pointscores")
        return [PointScore.model_validate(d) for d in data]

    def get_point_score_summary(self, score_id: int) -> PointScoreDetailsResponse:
        """
        Получает сводку по конкретной системе начисления очков.

        Args:
            score_id (int): ID системы очков.

        Returns:
            PointScoreDetailsResponse: Детализированная модель очков.
        """
        data: dict = self._get_json(f"/pointscores/{score_id}")
        return PointScoreDetailsResponse.model_validate(data)

    # =========================
    # Records
    # =========================

    def get_record_lists(self) -> RecordListResponse:
        """
        Получает список всех списков рекордов.

        Returns:
            RecordListResponse: Список моделей RecordItem.
        """
        data: list = self._get_json("/records")
        return [RecordItem.model_validate(d) for d in data]

    def get_records(
        self,
        record_list_id: int,
        include_all: bool = False,
    ) -> RecordsResponse:
        """
        Получает рекорды по конкретному списку рекордов.

        Args:
            record_list_id (int): ID списка рекордов.
            include_all (bool): Если True, возвращает все рекорды, иначе только текущие.

        Returns:
            RecordsResponse: Модель с рекордами.
        """
        suffix = "/all" if include_all else ""
        data: dict = self._get_json(f"/records/{record_list_id}{suffix}")
        return RecordsResponse.model_validate(data)

    def get_records_for_event(self, event: int) -> RecordsByEventResponse:
        """
        Получает рекорды, относящиеся к конкретному событию.

        Args:
            event (int | str): Номер или код события.

        Returns:
            RecordsByEventResponse: Список моделей RecordByEventItem.
        """
        data: list = self._get_json(f"/records/byevent/{event}")
        return [RecordByEventItem.model_validate(d) for d in data]

    # =========================
    # Time → points
    # =========================
    # ###               ####
    # ### Does not work ####
    # ###               ####
    #
    # def calculate_points(
    #     self,
    #     event_id: int,
    #     gender: int,
    #     swim_time: str,
    #     *,
    #     age: Optional[int] = None,
    #     handicap: Optional[int] = None,
    # ) -> int:
    #     """
    #     swim_time format: mm:ss.zz
    #     """
    #     params = {
    #         "eventid": event_id,
    #         "gender": gender,
    #         "time": swim_time,
    #     }
    #     if age is not None:
    #         params["age"] = age
    #     if handicap is not None:
    #         params["handicap"] = handicap

    #     data: int = self._get_json("/time2Points", params=params)
    #     return data

    # def calculate_handicap_points(
    #     self,
    #     event_id: int,
    #     gender: int,
    #     handicap: int,
    #     swim_time: str,
    # ) -> int:
    #     data: int = self._get_json(
    #         "/time2Points/handicap",
    #         params={
    #             "eventid": event_id,
    #             "gender": gender,
    #             "handicap": handicap,
    #             "time": swim_time,
    #         },
    #     )
    #     return data

    # def calculate_master_points(
    #     self,
    #     event_id: int,
    #     gender: int,
    #     age: int,
    #     swim_time: str,
    # ) -> int:
    #     data: int = self._get_json(
    #         "/time2Points/master",
    #         params={
    #             "eventid": event_id,
    #             "gender": gender,
    #             "age": age,
    #             "time": swim_time,
    #         },
    #     )
    #     return data
