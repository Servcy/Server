import decimal
import json
import logging
import random
import string
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Union

from django.conf import settings
from django.core import serializers
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Value as V
from django.db.models import When
from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)


class CommonUtils:
    def __init__(self):
        return

    @staticmethod
    def create_dict_from_queryset(query_set, key_name, data_type="queryset"):
        """
        :param query_set:
        :param key_name:
        :param data_type:
        :return: converted dictionary(dict)
        Function to create dictionary from queryset
        """
        result_dict = {}
        for item in query_set:
            key = getattr(item, key_name) if data_type == "queryset" else item[key_name]
            if key is not None:
                result_dict.setdefault(key, []).append(item)
        return result_dict

    @staticmethod
    def create_id_dict_from_queryset(query_set, data_type="queryset", key_type=None):
        """
        Function to create dictionary from queryset
        :param query_set:
        :param data_type:
        :param key_type: Can only be str, int or float
                        Eg: key_type = str or key_type=int or key_type=float
                        Note: These values are not in string, but the type instance itself
        :return: converted dictionary(dict)
        """
        result_dict = {}
        for item in query_set:
            key = getattr(item, "id") if data_type == "queryset" else item["id"]
            if key_type is not None:
                key = key_type(key)
            result_dict[key] = item
        return result_dict

    @staticmethod
    def format_date(date, date_type, only_date=None):
        """
        Function to format date
        :param date:
        :param date_type:
        :param only_date:
        :return: Formatted date (date)
        """
        try:
            if date_type == "start_date":
                date = (
                    datetime.strptime(date, settings.HUMAN_DATE_FORMAT)
                    + timedelta(days=0)
                ).date()
            elif date_type == "end_date":
                if only_date is not None:
                    date = (
                        datetime.strptime(date, settings.HUMAN_DATE_FORMAT)
                        + timedelta(days=0)
                    ).date()
                else:
                    date = (
                        datetime.strptime(date, settings.HUMAN_DATE_FORMAT)
                        + timedelta(days=1)
                    ).date()
        except:
            if date_type == "start_date":
                date = datetime.strptime(
                    "01/01/1900", settings.HUMAN_DATE_FORMAT
                ).date()
            elif date_type == "end_date":
                date = datetime.strptime(
                    "01/01/2100", settings.HUMAN_DATE_FORMAT
                ).date()
        return date

    @staticmethod
    def check_date(date_chk, return_none=False):
        try:
            if not date_chk:
                return None if return_none else "-"
            return date_chk.date().strftime(settings.HUMAN_DATE_FORMAT)
        except:
            return None

    @staticmethod
    def check_date_time(date_chk, return_blank=False):
        try:
            if not date_chk:
                return "" if return_blank else "-"

            return date_chk.strftime(settings.HUMAN_DATETIME_FORMAT)
        except:
            return "" if return_blank else "-"

    @staticmethod
    def check_object(object_instance):
        return None if not object_instance else object_instance.id

    @staticmethod
    def check_if_integer(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def check_string(string_chk, default_return="-"):
        return default_return if not string_chk else string_chk

    @staticmethod
    def check_number(number, round_off=5):
        try:
            return 0 if not number else round(float(number), round_off)
        except:
            return 0

    @staticmethod
    def paginate(object_list, page_size, current_page_no):
        """
        :param object_list: (any iterable object)
        :param page_size:
        :param current_page_no:
        :return: current_page, paginator_details (Access objects from current_page as :: current_page.object_list)
        """
        try:
            paginator = Paginator(object_list, page_size)
            current_page = paginator.page(current_page_no)
        except EmptyPage:
            current_page_no = 1
            paginator = Paginator(object_list, page_size)
            current_page = paginator.page(current_page_no)
        paginator_details = {
            "number": current_page.number,
            "has_previous": current_page.has_previous(),
            "has_next": current_page.has_next(),
            "num_pages": paginator.num_pages,
            "total_items": paginator.count,
        }
        return current_page, paginator_details

    @staticmethod
    def create_dict_from_queryset_allow_none(query_set, key_name, data_type="queryset"):
        """
        :param query_set:
        :param key_name:
        :param data_type
        :return: converted dictionary(dict)
        Function to create dictionary from queryset
        """
        result_dict = defaultdict(list)

        for item in query_set:
            key = getattr(item, key_name) if data_type == "queryset" else item[key_name]

            result_dict[key].append(item)

        return result_dict

    @staticmethod
    def get_uid(length: int = 10) -> str:
        """
        Function to generate and return uid.
        """
        return "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
        )

    @staticmethod
    def create_model_entries(
        dict_list,
        uid_list,
        model_name,
        uid_field_name="uid",
        select_related_entity=None,
        batch_size=None,
    ):
        model_object_list = [model_name(**data) for data in dict_list]
        if batch_size:
            model_name.objects.bulk_create(model_object_list, batch_size=batch_size)
        else:
            model_name.objects.bulk_create(model_object_list)
        uid_object_id_mapping = {}
        created_objects = []
        if uid_list:
            lookup = uid_field_name + "__in"
            created_objects = model_name.objects.filter(**{lookup: uid_list})
            if select_related_entity:
                created_objects = created_objects.select_related(select_related_entity)
            created_object_dict = CommonUtils.create_dict_from_queryset(
                created_objects, uid_field_name
            )
            for uid in uid_list:
                uid_object_id_mapping[uid] = created_object_dict[uid][0].id
        return created_objects, uid_object_id_mapping

    @staticmethod
    def replace_uid_in_dict_list(dict_list, replace_key_uid_mapping):
        """
        Function to replace uid in list of dictionary
        :param dict_list: [{'parent_process_id': 'uid_p_1', 'child_process_id': 'uid_c_1', 'name': 'RM1'}, {'parent_process_id': 'uid_p_2', 'child_process_id': 'uid_c_2', 'name': 'RM2'}]
        :param replace_key_uid_mapping: {'parent_process_id': {'uid_p_1': 1150, 'uid_p_2': 1151}, 'child_process_id': {'uid_c_1': 3480, 'uid_c_2': 3481}}
        :return: [{'parent_process_id': 1150, 'child_process_id': 3480, 'name': 'RM1'}, {'parent_process_id': 1151, 'child_process_id': 3481, 'name': 'RM2'}]
        """
        for dictionary in dict_list:
            for replace_key, uid_mapping in replace_key_uid_mapping.items():
                dictionary[replace_key] = (
                    uid_mapping[dictionary[replace_key]]
                    if dictionary[replace_key] is not None
                    else None
                )
        return dict_list

    @staticmethod
    def prepare_case_when_for_bulk_operation(dictionary, primary_key="pk"):
        """
        Function to prepare When statement from dictionary.

        :param dictionary:
        :param primary_key:
        :return:
        """
        when_criteria = [
            When(**{primary_key: key}, then=V(value))
            for key, value in dictionary.items()
        ]
        return when_criteria

    @staticmethod
    def get_states_mapping(state):
        """
        :param state:
        :return:
        """
        return settings.STATES_MAPPING.get(state, state)

    @staticmethod
    def get_value(data, keys, default_val, val_type):
        """
        :param default_val:
        :param data: source object -> dict
        :param keys: list of keys to check for
        :param val_type: type of the return type [int, str]
        :return:
        """
        for key in keys:
            value = getattr(data, key, None)
            if value:
                return val_type(value)

        return default_val

    @staticmethod
    def get_positive_or_zero_number(
        value: Union[int, float, Decimal]
    ) -> Union[int, float, Decimal]:
        """
        :param value:
        :return:
        """
        if value and value > 0:
            return value

        return 0

    @staticmethod
    def log_time_data_in_func(
        time_dict=None, line_no=None, print_output=False, logger_obj=None, ref_text=""
    ):
        """
        :param time_dict:
        :param line_no:
        :param print_output:
        :param logger_obj:
        :param ref_text:
        :return:
        """
        if not time_dict:
            time_dict = {"current_index": 1}

        time_dict[time_dict["current_index"]] = {
            "time": datetime.now(),
            "line_no": line_no if line_no else "",
            "ref_text": ref_text,
        }

        if print_output:
            if time_dict["current_index"] > 1:
                for i in range(2, time_dict["current_index"] + 1):
                    logger_obj.info(
                        "Time"
                        + str(i)
                        + " - Time"
                        + str(i - 1)
                        + "::: Line No::"
                        + str(time_dict[i]["line_no"])
                        + " - "
                        + str(time_dict[i - 1]["line_no"])
                        + ":::"
                        + "::: Ref Text::"
                        + str(time_dict[i]["ref_text"])
                        + " - "
                        + str(time_dict[i - 1]["ref_text"])
                        + ":::"
                        + str(
                            (
                                time_dict[i]["time"] - time_dict[i - 1]["time"]
                            ).total_seconds()
                        )
                    )
            else:
                logger_obj.info("Time1::" + str(time_dict[1]["time"]))

        time_dict["current_index"] += 1

        return time_dict

    @staticmethod
    def dict_from_model_with_values(model_input):
        """
        Get values of the Model in the form of dict.
        :param modelinput:
        :return list of dicts with all values
        """
        values = json.loads(serializers.serialize("json", model_input))
        new_values = []
        for val in values:
            new_values.append({**val["fields"], "id": val["pk"]})
        return new_values

    @staticmethod
    def dict_from_model_object(model_object) -> Dict[str, Any]:
        """
        Get values of the Model in the form of dict.
        :param model_object: A model object.
        :return: dict with all values of the object except the state and internal values.
        """
        model_dict: Dict[str, Any] = model_object.__dict__
        initial_keys = list(model_dict.keys())
        for key in initial_keys:
            if key.startswith("_"):
                del model_dict[key]
        return model_dict
