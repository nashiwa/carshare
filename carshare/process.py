def process_list(result):
    process_result = []
    if result is not None:
        for item in result:
            k = list(item)
            process_result.append(k)
        return process_result
    else:
        return process_result


def make_single_list(result):
    data = []
    if result is not None:
        for item in result:
            data.append(item)
    return data


def dictfetchall(cur):
    results = []
    for row in cur.fetchall():
        results.append(dict(zip(columns, row)))
    return results