from ...financial.model import StripeCountry


def get_date_format(country):
    if country == StripeCountry.US:
        # US time file_format AM/PM
        return "MM/DD/YYYY, hh:mm A"

    # 24 hour clock
    return "DD/MM/YYYY, HH:mm"


def get_currency(country):
    print(country)
    match country:
        case StripeCountry.US:
            return "usd"
        case StripeCountry.GB:
            return "gbp"
        case StripeCountry.AU:
            return "aud"
        case StripeCountry.CA:
            return "cad"
        case _:
            return "eur"
