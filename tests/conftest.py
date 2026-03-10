
import logging

# import pytest
# from contextlib import nullcontext as does_not_raise

# # (assuming check_user function is defined above)

# @pytest.mark.parametrize(
#     "name, expected_exception, expected_result",
#     [
#         ("Yana", does_not_raise(), "Username is properly set"),
#         ("Bob", pytest.raises(ValueError, match="Invalid User"), None),
#     ],
# )
# def test_check_user_parametrized(name, expected_exception, expected_result):
#     with expected_exception:
#         result = check_user(name)
#         if expected_result is not None:
#             assert result == expected_result
