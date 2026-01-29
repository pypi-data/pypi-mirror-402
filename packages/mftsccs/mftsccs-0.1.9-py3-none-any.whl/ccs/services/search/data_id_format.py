"""
DataIdFormat - Formatting functions for converting graph data to JSON.

This module implements the three-pass formatting process for converting
concepts and connections into nested JSON structures.

The format produces output like:
[
    {
        "id": 123,
        "data": {
            "the_person": {
                "the_name": {"id": 1, "data": {"the_name": "John"}},
                "the_email": {"id": 2, "data": {"the_email": "john@example.com"}}
            }
        },
        "created_on": "2024-01-01T00:00:00"
    }
]
"""

from typing import Any, Dict, List
from ccs.models.connection import Connection
from ccs.services.search.count_info import CountInfo


async def format_connections_data_id(
    linkers: List[int],
    concept_ids: List[int],
    main_composition_ids: List[int],
    reverse: List[int],
    count_infos: List[CountInfo],
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    """
    Main entry point for formatting connections to DATA-ID format.

    This function converts graph concepts and connections to a nested JSON format
    that includes both IDs and data for each concept.

    Args:
        linkers: List of connection IDs (linker connections)
        concept_ids: List of concept IDs in the result
        main_composition_ids: List of main composition IDs (root entities)
        reverse: List of connection IDs that should be processed in reverse
        count_infos: List of CountInfo objects for aggregation data
        order: Sort order - "ASC" or "DESC"

    Returns:
        List of formatted composition dictionaries

    Example:
        >>> result = await format_connections_data_id(
        ...     linkers=[1, 2, 3],
        ...     concept_ids=[100, 101, 102],
        ...     main_composition_ids=[100],
        ...     reverse=[],
        ...     count_infos=[],
        ...     order="DESC"
        ... )
        >>> print(result[0]["id"])  # 100
    """
    from ccs.services.search.prefetch import get_connection_data_prefetch
    from ccs.services.search.ordering import order_connections

    # Step 1: Prefetch all connections and related concepts
    prefetch_connections = await get_connection_data_prefetch(linkers)

    # Step 2: Order connections
    prefetch_connections = order_connections(prefetch_connections, order)

    # Step 3: Initialize composition data structures (Pass 1)
    composition_data: Dict[int, Any] = {}
    composition_data = await format_function_data(prefetch_connections, composition_data, reverse)

    # Step 4: Add nested data with IDs (Pass 2)
    composition_data = await format_function_data_for_data(prefetch_connections, composition_data, reverse)

    # Step 5: Stitch together final output (Pass 3)
    output = await format_from_connections_altered_array_external(
        prefetch_connections,
        composition_data,
        main_composition_ids,
        reverse
    )

    return output


async def format_function_data(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    reverse: List[int]
) -> Dict[int, Any]:
    """
    Pass 1: Initialize empty concept structures indexed by ID.

    This pass creates the basic structure for each concept, initializing
    empty dictionaries keyed by the concept's type.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary to populate (mutated in place)
        reverse: List of connection IDs to process in reverse

    Returns:
        Updated composition_data dictionary
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    # Collect all concept IDs (matching TypeScript pattern)
    my_concepts: List[int] = []
    for connection in connections:
        my_concepts.append(connection.toTheConceptId)
        my_concepts.append(connection.ofTheConceptId)
        my_concepts.append(connection.typeId)

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)

        if reverse_flag:
            if of_concept.id != 0 and to_concept.id != 0:
                linker_concept = await GetTheConcept(connection.typeId)
                key = to_concept.type.characterValue if to_concept.type else "self"

                if connection.toTheConceptId in composition_data:
                    new_data = composition_data[connection.toTheConceptId]
                else:
                    new_data = {}
                    new_data[key] = {}
                    composition_data[connection.toTheConceptId] = new_data

                try:
                    my_type = of_concept.type.characterValue if of_concept.type else "none"
                    value = of_concept.characterValue
                    reverse_character = linker_concept.characterValue + "_reverse"

                    if "_s_" in reverse_character:
                        if of_concept.id not in composition_data:
                            composition_data[of_concept.id] = {}
                        composition_data[of_concept.id][my_type] = value

                    composition_data[to_concept.id] = {}

                except Exception as ex:
                    print("this is error", ex)
        else:
            if of_concept.id != 0 and to_concept.id != 0:
                linker_concept = await GetTheConcept(connection.typeId)
                key = of_concept.type.characterValue if of_concept.type else "self"

                if connection.ofTheConceptId in composition_data:
                    new_data = composition_data[connection.ofTheConceptId]
                else:
                    new_data = {}
                    new_data[key] = {}
                    composition_data[connection.ofTheConceptId] = new_data

                try:
                    my_type = to_concept.type.characterValue if to_concept.type else "none"
                    value = to_concept.characterValue

                    if "_s_" in linker_concept.characterValue:
                        if to_concept.id not in composition_data:
                            composition_data[to_concept.id] = {}
                        composition_data[to_concept.id][my_type] = value

                    composition_data[of_concept.id] = {}

                except Exception as ex:
                    print("this is error", ex)

    return composition_data


def _remove_the_prefix(s: str) -> str:
    """Remove 'the_' prefix from a string if present."""
    if s.startswith("the_"):
        return s[4:]
    return s


def _is_numeric_string(s: str) -> bool:
    """Check if a string is numeric (matches isNaN(Number(x)) === false in JS)."""
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


async def format_function_data_for_data(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    reverse: List[int]
) -> Dict[int, Any]:
    """
    Pass 2: Add detailed data properties with ID and data structure.

    This pass populates the nested data structure with actual concept values,
    creating objects with "id" and "data" keys.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary to update (mutated in place)
        reverse: List of connection IDs to process in reverse

    Returns:
        Updated composition_data dictionary
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    # Collect all concept IDs (matching TypeScript pattern)
    my_concepts: List[int] = []
    for connection in connections:
        my_concepts.append(connection.toTheConceptId)
        my_concepts.append(connection.ofTheConceptId)
        my_concepts.append(connection.typeId)

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)

        if reverse_flag:
            if of_concept.id != 0 and to_concept.id != 0:
                linker_concept = await GetTheConcept(connection.typeId)
                key = to_concept.type.characterValue if to_concept.type else "self"

                if connection.toTheConceptId in composition_data:
                    new_data = composition_data[connection.toTheConceptId]
                    if key not in new_data:
                        new_data[key] = {}
                else:
                    new_data = {}
                    new_data[key] = {}
                    composition_data[connection.toTheConceptId] = new_data

                try:
                    my_type = of_concept.type.characterValue if of_concept.type else "none"
                    value = of_concept.characterValue
                    data_character = linker_concept.characterValue

                    # if there is no connection type defined then put the type of the destination concept
                    if data_character == "":
                        data_character = my_type
                        data_character = _remove_the_prefix(data_character)

                    data = {
                        "id": of_concept.id,
                        "data": {
                            my_type: value
                        }
                    }
                    reverse_character = data_character + "_reverse"

                    if "_s_" in reverse_character:
                        # do nothing
                        pass
                    else:
                        if isinstance(new_data[key], str):
                            new_data[key] = {}
                        new_data[key][reverse_character] = data

                except Exception as ex:
                    print("this is error", ex)
        else:
            if of_concept.id != 0 and to_concept.id != 0:
                linker_concept = await GetTheConcept(connection.typeId)
                key = of_concept.type.characterValue if of_concept.type else "self"

                if connection.ofTheConceptId in composition_data:
                    new_data = composition_data[connection.ofTheConceptId]
                    if key not in new_data:
                        new_data[key] = {}
                else:
                    new_data = {}
                    new_data[key] = {}
                    composition_data[connection.ofTheConceptId] = new_data

                try:
                    my_type = to_concept.type.characterValue if to_concept.type else "none"
                    value = to_concept.characterValue
                    data_character = linker_concept.characterValue
                    is_comp = False

                    # if there is no connection type defined then put the type of the destination concept
                    if data_character == "":
                        data_character = my_type
                        data_character = _remove_the_prefix(data_character)
                        is_comp = True

                    data = {
                        "id": to_concept.id,
                        "data": {
                            my_type: value
                        }
                    }

                    if not _is_numeric_string(data_character):
                        if "_s_" in data_character:
                            # do nothing
                            pass
                        else:
                            if isinstance(new_data[key], str):
                                new_data[key] = {}
                            new_data[key][data_character] = data
                    else:
                        if isinstance(new_data[key], list):
                            new_data[key].append(data)
                        else:
                            new_data[key] = []
                            new_data[key].append(data)

                except Exception as ex:
                    print("this is error", ex)

    return composition_data


async def format_from_connections_altered_array_external(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    main_composition_ids: List[int],
    reverse: List[int]
) -> List[Dict[str, Any]]:
    """
    Pass 3: Stitch compositions together with timestamps and create final output.

    This pass links child compositions to parent compositions and builds
    the final array of main composition objects.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary of composition data from previous passes
        main_composition_ids: List of IDs for the main/root compositions
        reverse: List of connection IDs to process in reverse

    Returns:
        List of formatted main composition dictionaries
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    main_data: List[Dict[str, Any]] = []

    # Collect all concept IDs (matching TypeScript pattern)
    my_concepts: List[int] = []
    for connection in connections:
        my_concepts.append(connection.toTheConceptId)
        my_concepts.append(connection.ofTheConceptId)
        my_concepts.append(connection.typeId)

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)

        if reverse_flag:
            if of_concept.id != 0 and to_concept.id != 0:
                if to_concept.id in composition_data:
                    linker_concept = await GetTheConcept(connection.typeId)
                    key = to_concept.type.characterValue if to_concept.type else "self"
                    flag = False

                    if connection.toTheConceptId in composition_data:
                        flag = True

                    if connection.toTheConceptId in composition_data:
                        new_data = composition_data[connection.toTheConceptId]
                        new_type = type(new_data.get(key))
                        if new_type == str:
                            new_data[key] = {}
                    else:
                        new_data = {}
                        new_data[key] = {}
                        composition_data[connection.toTheConceptId] = new_data

                    try:
                        is_comp = composition_data.get(connection.ofTheConceptId)
                        if is_comp:
                            data = {
                                "id": of_concept.id,
                                "data": composition_data[connection.ofTheConceptId],
                                "created_on": connection.entryTimeStamp
                            }
                            reverse_character = linker_concept.characterValue + "_reverse"

                            if isinstance(new_data[key].get(reverse_character), list):
                                new_data[key][reverse_character].append(data)
                            else:
                                if "_s_" in reverse_character:
                                    new_data[key][reverse_character] = []
                                    new_data[key][reverse_character].append(data)
                                else:
                                    new_data[key][reverse_character] = data

                    except Exception as ex:
                        print("this is error", ex)

        # Forward direction - processed for ALL connections (not in else block)
        if of_concept.id != 0 and to_concept.id != 0:
            if of_concept.id in composition_data:
                linker_concept = await GetTheConcept(connection.typeId)
                key = of_concept.type.characterValue if of_concept.type else "self"
                flag = False

                if connection.toTheConceptId in composition_data:
                    flag = True

                if connection.ofTheConceptId in composition_data:
                    new_data = composition_data[connection.ofTheConceptId]
                    new_type = type(new_data.get(key))
                    if new_type == str:
                        new_data[key] = {}
                else:
                    new_data = {}
                    new_data[key] = {}
                    composition_data[connection.ofTheConceptId] = new_data

                is_comp = True
                linker_concept_value = linker_concept.characterValue
                if linker_concept_value == "":
                    linker_concept_value = to_concept.characterValue
                    is_comp = True
                if linker_concept_value == "":
                    linker_concept_value = to_concept.type.characterValue if to_concept.type else ""

                try:
                    my_type = to_concept.type.characterValue if to_concept.type else "none"
                    my_data = composition_data.get(connection.toTheConceptId)

                    if my_data:
                        data = {
                            "id": to_concept.id,
                            "data": composition_data[connection.toTheConceptId],
                            "created_on": connection.entryTimeStamp
                        }

                        if isinstance(new_data[key], list):
                            if is_comp:
                                new_data[key].append(my_data)
                            else:
                                new_data[key].append(my_data)
                        else:
                            if isinstance(new_data[key].get(linker_concept_value), list):
                                new_data[key][linker_concept.characterValue].append(data)
                            else:
                                if "_s_" in linker_concept_value:
                                    new_data[key][linker_concept_value] = []
                                    new_data[key][linker_concept_value].append(data)
                                else:
                                    new_data[key][linker_concept_value] = data

                except Exception as ex:
                    print("this is error", ex)

    # Build final output for main compositions
    for main_id in main_composition_ids:
        my_main_data: Dict[str, Any] = {}
        my_main_data["id"] = main_id
        my_main_data["data"] = composition_data.get(main_id, {})
        main_data.append(my_main_data)

    return main_data
