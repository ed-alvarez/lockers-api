from sqlalchemy.exc import IntegrityError


def format_error(e: IntegrityError) -> str:
    try:
        # * Build the first part of the error message
        statements = e.statement.split(" ")
        verb = statements[0].lower()  # INSERT, UPDATE, DELETE
        if verb == "insert":
            verb = "create"
        # Table name, if UPDATE, the table name is the second element in the list
        resource = statements[1] if verb == "update" else statements[2]

        # * Build the second part of the error message
        root = f"{e.orig}".split(") ").pop()  # Extract the root of the detail
        root_elements = root.split('"')
        detail = root_elements[0].strip()
        target = root_elements[1].capitalize()

        # * filter the target, in case it's a link table
        target = target.split("_")
        target = target.pop().capitalize()

        if detail == "is not present in table":
            statement = f"the selected {target} does not exist"
        elif detail == "is still referenced from table":
            statement = f"one or more {target}s are still referenced to it"
        else:
            statement = f"{target} {detail}"

        error_message = f"Cannot {verb} {resource.capitalize()}, {statement}"
    except Exception:
        return e.orig

    return error_message
