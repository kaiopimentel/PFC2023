def get_zone_number(latitude, longitude):
    if 56 <= latitude < 64 and 3 <= longitude < 12:
        return 32
    if 72 <= latitude <= 84 and longitude >= 0:
        if longitude < 9:
            return 31
        elif longitude < 21:
            return 33
        elif longitude < 33:
            return 35
        elif longitude < 42:
            return 37
    if latitude >= 0:
        return (str(int((longitude + 180) / 6) + 1) + "N")
    else:
        return (str(int((longitude + 180) / 6) + 1) + "S")