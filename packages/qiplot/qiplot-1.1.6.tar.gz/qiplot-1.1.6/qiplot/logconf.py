[loggers]
keys=root

[handlers]
keys=console

[formatters]
keys=std_out

[logger_root]
handlers = console
level = DEBUG

[handler_console]
class = logging.StreamHandler
level = INFO
formatter = std_out

[formatter_std_out]
format = %(levelname)s : %(module)s : line %(lineno)03d : %(message)s
