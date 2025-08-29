import zen
import csv
import pytest
from pathlib import Path 

base_data_dir = Path(__file__).parent / "data"

def read_csv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # 跳过标题行
        for row in reader:
            # 跳过空行和带#的描述行
            if not row or row[0].strip().startswith('#'):
                continue
            if len(row) == 3:
                # 提取有效行数据（expression、input、output）
                expression = row[0].strip()
                input_data = row[1].strip()
                output_data = row[2].strip()
                data.append({
                    'expression': expression,
                    'input': input_data,
                    'output': output_data
                })
            elif len(row) == 2:
                # 提取有效行数据（expression、output）
                expression = row[0].strip()
                output_data = row[1].strip()
                data.append({
                    'expression': expression,
                    'output': output_data
                })
    return data


@pytest.fixture()
def parsed_date_csv():
    file_path  = base_data_dir / "date.csv"
    parsed_data = read_csv(file_path)
    return parsed_data


@pytest.fixture()
def parsed_standard_csv():
    file_path  = base_data_dir / "standard.csv"
    parsed_data = read_csv(file_path)
    return parsed_data


@pytest.fixture()
def parsed_unary_csv():
    file_path  = base_data_dir / "unary.csv"
    parsed_data = read_csv(file_path)
    return parsed_data


def test_zen_date_expression(parsed_date_csv):
    for data in parsed_date_csv:
        input = data.get("input", "")
        expression = data["expression"]
        output = data["output"] if data["output"] else None
        output = zen.evaluate_expression("d({})".format(output)) if "Z" in output else zen.evaluate_expression(output)
        input = zen.evaluate_expression(input) if input else None
        re = zen.evaluate_expression(expression, input)
        assert re == output


def test_zen_standard_expression(parsed_standard_csv):
    for data in parsed_standard_csv:
        input = data.get("input", "")
        expression = data["expression"]
        input = zen.evaluate_expression(input) if input else None
        output = data["output"] if data["output"] else None
        re = zen.evaluate_expression(expression, input)
        assert re == zen.evaluate_expression(output)


def test_zen_unary_expression(parsed_unary_csv):
    for data in parsed_unary_csv:
        input = data.get("input", "")
        expression = data["expression"]
        input = zen.evaluate_expression(input) if input else None
        output = zen.evaluate_expression(data["output"]) if data["output"] else None
        re = zen.evaluate_unary_expression(expression, input)
        assert re == output
