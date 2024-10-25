def convert_to_pounds(weight_value: str, weight_unit: str) -> float:
    if weight_value == "no_weight":
        return 1.0

    try:
        value = float(weight_value.replace(",", "."))
        if weight_unit == "g":
            return value / 453.592
        elif weight_unit == "kg":
            return value * 2.20462
        elif weight_unit == "oz":
            return value / 16
        elif weight_unit == "lb":
            return value
        else:
            return 1.0
    except ValueError:
        return 1.0


SHIPPING_RATES = {
    "Books": {"base": 3.99, "per_pound": 0},
    "CDs, Cassettes, Vinyl": {"base": 3.99, "per_pound": 0},
    "VHS Videotapes": {"base": 3.99, "per_pound": 0},
    "DVDs and Blu-ray": {"base": 3.99, "per_pound": 0},
    "Video Games": {"base": 3.99, "per_pound": 0},
    "Software & Computer Games": {"base": 3.99, "per_pound": 0},
    "Camera & Photo": {"base": 4.49, "per_pound": 0.50},
    "Tools & Hardware": {"base": 4.49, "per_pound": 0.50},
    "Kitchen & Housewares": {"base": 4.49, "per_pound": 0.50},
    "Computer": {"base": 4.49, "per_pound": 0.50},
    "Outdoor Living": {"base": 4.49, "per_pound": 0.50},
    "Electronics": {"base": 4.49, "per_pound": 0.50},
    "Sports & Outdoors": {"base": 4.49, "per_pound": 0.50},
    "Cell Phones & Service": {"base": 4.49, "per_pound": 0.50},
    "Musical Instruments": {"base": 4.49, "per_pound": 0.50},
    "Office Products": {"base": 4.49, "per_pound": 0.50},
    "Toy & Baby": {"base": 4.49, "per_pound": 0.50},
    "Independent Design items": {"base": 0, "per_pound": 0},
    "Everything Else": {"base": 4.49, "per_pound": 0.50},
}


def calculate_shipping_fee(category: str, weight_lb: float) -> float:
    rates = SHIPPING_RATES[category]
    return rates["base"] + (rates["per_pound"] * weight_lb)
