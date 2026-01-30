import datetime


def _release_schedule() -> tuple:
    """Chromium release schedule

    https://chromiumdash.appspot.com/schedule
    """
    schedule = (
        ('Feb 2, 2027', 157),
        ('Jan 5, 2027', 156),
        ('Nov 17, 2026', 155),
        ('Oct 20, 2026', 154),
        ('Sep 22, 2026', 153),
        ('Aug 25, 2026', 152),
        ('Jul 28, 2026', 151),
        ('Jun 30, 2026', 150),
        ('Jun 2, 2026', 149),
        ('May 5, 2026', 148),
        ('Apr 7, 2026', 147),
        ('Mar 10, 2026', 146),
        ('Feb 10, 2026', 145),
        ('Jan 13, 2026', 144)
    )

    return schedule


def _major_version(now: datetime.datetime | None = None) -> int:
    """Major version of Chrome Browser"""

    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    schedule = _release_schedule()
    version = schedule[len(schedule)-1][1] - 1

    for item in schedule:
        if now.date() > datetime.datetime.strptime(item[0], '%b %d, %Y').date():
            version = item[1]
            break

    return version


def _unified_platform() -> str:
    """platform part of user-agent

    macOS:   'Macintosh; Intel Mac OS X 10_15_7'
    windows: 'Windows NT 10.0; Win64; x64'
    linux:   'X11; Linux x86_64'

    https://chromium.googlesource.com/chromium/src.git/+/refs/heads/main/content/common/user_agent.cc
    """
    platform = 'Macintosh; Intel Mac OS X 10_15_7'

    return platform


def user_agent(major_ver: int | None = None) -> str:
    """Return the user-agent of Chrome Browser"""

    if major_ver is None:
        major_ver = _major_version()

    agent = 'Mozilla/5.0 ({}) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/{}.0.0.0 Safari/537.36'

    return agent.format(_unified_platform(), major_ver)
