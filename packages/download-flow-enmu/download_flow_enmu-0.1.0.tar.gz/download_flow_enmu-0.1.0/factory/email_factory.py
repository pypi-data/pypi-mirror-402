from strategy.email.gmail import Gmail


def create_emial(email: str, auth_config: dict, auth_type: str):
    if email == "gmail" and auth_type == "pass":
        return Gmail(
            username=auth_config.get("username", ""),
            password=auth_config.get("password", ""),
        )
    else:
        raise NameError("未知邮箱")
