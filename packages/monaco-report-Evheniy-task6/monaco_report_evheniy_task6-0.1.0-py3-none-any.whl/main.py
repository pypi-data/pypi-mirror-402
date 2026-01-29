from report_package.table_racers import build_report, print_report

def main():
    """entry point to the program"""
    start_data = build_report('data_files/start.log')
    end_data = build_report('data_files/end.log')
    drivers_info =  print_report('data_files/abbreviations.txt')

    report = []

    for abbr, info in drivers_info.items():
        start_time = start_data[abbr]
        end_time = end_data[abbr]
        lap_time = abs(end_time - start_time)
        report.append([abbr, info[0], info[1], lap_time])

    report.sort(key=lambda x: x[2])

    print("Table racers")
    print("=" * 50)
    for i, drivers_info in enumerate(report, 1):
        abbr = drivers_info[0]
        name = drivers_info[1]
        team = drivers_info[2]
        lap_time = drivers_info[3]
        print(f"{i:<2}. {abbr} | {name:<20} | {team:<25} | {str(lap_time)[2:-3]}")
        if i == 15:
            print("_" * 50)

if __name__ == '__main__':
    main()