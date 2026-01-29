from functools import wraps
from loguru import logger


def log_operation(func):
    """작업을 로깅하기 위한 데코레이터
    이 데코레이터는 함수의 시작과 완료를 로깅합니다.
    함수 실행 중 발생하는 예외도 로깅하여 디버깅을 용이하게 합니다.

    Args:
        func (Callable): 로깅을 적용할 함수

    Returns:
        Callable: 로깅 기능이 추가된 함수
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Starting {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper
