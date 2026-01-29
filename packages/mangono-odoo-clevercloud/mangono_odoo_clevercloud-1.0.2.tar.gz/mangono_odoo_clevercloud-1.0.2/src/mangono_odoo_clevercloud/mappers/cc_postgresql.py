from environ_odoo_config.environ import Environ


def clevercloud_postgresql(curr_env: Environ) -> Environ:
    return clevercloud_postgresql_classic(clevercloud_direct_host(curr_env))


def clevercloud_postgresql_classic(curr_env: Environ) -> Environ:
    """ """
    return curr_env + {
        "DB_NAME": curr_env.gets("DB_NAME", "POSTGRESQL_ADDON_DB"),
        "DB_HOST": curr_env.gets("DB_HOST", "POSTGRESQL_ADDON_HOST"),
        "DB_PORT": curr_env.gets("DB_PORT", "POSTGRESQL_ADDON_PORT"),
        "DB_USER": curr_env.gets("DB_USER", "POSTGRESQL_ADDON_USER"),
        "DB_PASSWORD": curr_env.gets("DB_PASSWORD", "POSTGRESQL_ADDON_PASSWORD"),
    }


def clevercloud_direct_host(curr_env: Environ) -> Environ:
    """ """
    return curr_env + {
        "DB_HOST": curr_env.gets("DB_HOST", "POSTGRESQL_ADDON_DIRECT_HOST"),
        "DB_PORT": curr_env.gets("DB_PORT", "POSTGRESQL_ADDON_DIRECT_PORT"),
    }
