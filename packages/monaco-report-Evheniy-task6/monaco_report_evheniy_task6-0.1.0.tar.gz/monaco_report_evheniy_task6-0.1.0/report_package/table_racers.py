from datetime import datetime

start_log = "data_files/start.log"
end_log = "data_files/end.log"


def build_report(path):
    """
    reads log files and returns a dictionary with datetime objects
    :param path: path to file(start.log or end.log)
    :return: dictionary {ABBR: datetime_object}.
    """
    data = {}
    with open(path, "r", encoding="utf=8") as f:
        for line in f:
            line = line.strip()
            if not line:continue
            abbr = line[:3]
            time_str = line[3:]
            t_obj = datetime.strptime(time_str, "%Y-%m-%d_%H:%M:%S.%f")
            data[abbr] = t_obj

    return data


def print_report(filename):
    """
    reads log files and returns a dictionary with datetime objects
    :param filename: path to abbreviations.txt
    :return: dictionary {ABBR: [name, team]}.
    """
    driver_list = {}
    with open(filename, "r", encoding="utf=8") as f:
        for line in f:
            line = line.strip()
            if not line:continue
            parts = line.split("_")
            driver_list[parts[0]] = parts[1], parts[2]
    return driver_list