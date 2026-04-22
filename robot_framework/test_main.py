"""
THIS IS A TEST SCRIPT
"""

import os
import sys
import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from mbu_dev_shared_components.getorganized.objects import CaseDataJson
from goAPI.case_handler import CaseHandler
from goAPI.file_handler import FileHandler
from goAPI import helper_functions
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


LINE_BREAK = "\n\n\n------------------------------------------------------------------------------------------------------------------\n\n\n"


class DatabaseError(Exception):
    """Custom exception for database related errors."""


class RequestError(Exception):
    """Custom exception for request related errors."""


def identify_employee_folders(
    case_handler: CaseHandler,  # A handler to interact with the case management system
    case_data_handler: CaseDataJson,  # A handler to interact with case data in JSON format - this handler helps create the json data, used in the case_handler
    case_type: str,  # The type of case to be handled (e.g., "PER" for employee cases)
    case_title: str,  # The title of the case to be handled (e.g., "Lønbilag" for salary cases)
    cpr_dicts: str, # SELV - det CPR-nummer der skal slås op
):
    """
    main func
    """

    # Iterate through each CPR number and its associated data in the dictionary
    for i, (cpr, data) in enumerate(cpr_dicts.items()):
        # Initialize the salary_case_id variable to None for each iteration, so we can freely manipulate it later
        salary_case_id = None

        # Retrieve the employee's name and ID from the case handler using the CPR number
        person_full_name, person_go_id = helper_functions.contact_lookup(case_handler=case_handler, ssn=cpr)

        # This dictionary contains the properties we want to use, when searching for the case folder
        properties_for_case_search = {
            "ows_Title": case_title,
        }

        # Attempt 1: Check case folder with initial parameters
        # In the 1st attempt, we include the name in the search, as we want to find the case folder for this specific person, and we also include the case_title as a field property to narrow down the search
        print("Attempt 1")
        salary_case_info = helper_functions.check_case_folder(
            case_data_handler=case_data_handler,
            case_handler=case_handler,
            case_type=case_type,
            person_full_name=person_full_name,
            person_go_id=person_go_id,
            ssn=cpr,
            include_name=True,
            returned_cases_number="25",
            field_properties=properties_for_case_search
        )

        #No fallback to ensure we always hit the corret tjenestenummer
        if not salary_case_info:
            raise LookupError(
                f"Fandt ingen sag for CPR {cpr} med title='{case_title}' på tjenestenummer {tjenestenummer}"
            )

        # In some cases, the search might return more than one case folder, if the person has multiple employment codes
        if len(salary_case_info) > 0:

            tjenestenummer = data.get("tjenestenummer")

            # If that is the case, we need to identify the correct case folder by using the employment code (tjenestenummer) from the Excel file
            salary_case_id = helper_functions.identify_correct_case_by_employment_code(case_handler=case_handler, salary_case_info=salary_case_info, tjenestenummer=tjenestenummer)
            print('Salary case id: ',salary_case_id)
            if not salary_case_id:
                raise LookupError(
                    f"Fandt sager for CPR {cpr}, men ingen matcher tjenestenummer {tjenestenummer}"
                )

#            else:
#                salary_case_id = None

        if salary_case_id:
            mapping_entry = {cpr: salary_case_id}

        else:
            mapping_entry = {cpr: "CPR NOT PROPERLY HANDLED - Please investigate this SSN"}

        # Limit the number of iterations for testing purposes
        if i > 10:
            break

    return salary_case_id