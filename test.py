x = {
    "token": "{'access_token': 'ghu_y2XLjP6B5WCC5nFA7w3IOF0XS4mTxo4CwBmi', 'scope': '', 'token_type': 'bearer'}",
    "user_info": "{'login': 'gargmegham', 'id': 95271253, 'node_id': 'U_kgDOBa25VQ', 'avatar_url': 'https://avatars.githubusercontent.com/u/95271253?v=4', 'gravatar_id': '', 'url': 'https://api.github.com/users/gargmegham', 'html_url': 'https://github.com/gargmegham', 'followers_url': 'https://api.github.com/users/gargmegham/followers', 'following_url': 'https://api.github.com/users/gargmegham/following{/other_user}', 'gists_url': 'https://api.github.com/users/gargmegham/gists{/gist_id}', 'starred_url': 'https://api.github.com/users/gargmegham/starred{/owner}{/repo}', 'subscriptions_url': 'https://api.github.com/users/gargmegham/subscriptions', 'organizations_url': 'https://api.github.com/users/gargmegham/orgs', 'repos_url': 'https://api.github.com/users/gargmegham/repos', 'events_url': 'https://api.github.com/users/gargmegham/events{/privacy}', 'received_events_url': 'https://api.github.com/users/gargmegham/received_events', 'type': 'User', 'site_admin': False, 'name': 'Megham Garg', 'company': 'Servcy', 'blog': 'https://meghamgarg.com', 'location': 'India', 'email': None, 'hireable': None, 'bio': 'Building Servcy', 'twitter_username': 'garg_megham', 'public_repos': 17, 'public_gists': 0, 'followers': 2, 'following': 0, 'created_at': '2021-11-30T06:04:02Z', 'updated_at': '2023-08-15T10:04:36Z'}",
}
yy = {
    "action": "updated",
    "security_advisory": {
        "ghsa_id": "GHSA-73qw-ww62-m54x",
        "cve_id": "CVE-2015-7541",
        "summary": "colorscore Command Injection vulnerability",
        "description": "The initialize method in the Histogram class in `lib/colorscore/histogram.rb` in the colorscore gem before 0.0.5 for Ruby allows context-dependent attackers to execute arbitrary code via shell metacharacters in the (1) `image_path`, (2) `colors`, or (3) `depth` variable.",
        "severity": "critical",
        "identifiers": [
            {"value": "GHSA-73qw-ww62-m54x", "type": "GHSA"},
            {"value": "CVE-2015-7541", "type": "CVE"},
        ],
        "references": [
            {"url": "https://nvd.nist.gov/vuln/detail/CVE-2015-7541"},
            {
                "url": "https://github.com/quadule/colorscore/commit/570b5e854cecddd44d2047c44126aed951b61718"
            },
            {"url": "http://rubysec.com/advisories/CVE-2015-7541/"},
            {"url": "http://www.openwall.com/lists/oss-security/2016/01/05/2"},
            {
                "url": "https://github.com/rubysec/ruby-advisory-db/blob/master/gems/colorscore/CVE-2015-7541.yml"
            },
            {"url": "http://seclists.org/oss-sec/2016/q1/17"},
            {"url": "https://github.com/advisories/GHSA-73qw-ww62-m54x"},
        ],
        "published_at": "2017-10-24T18:33:36Z",
        "updated_at": "2023-08-29T11:49:05Z",
        "withdrawn_at": None,
        "vulnerabilities": [
            {
                "package": {"ecosystem": "rubygems", "name": "colorscore"},
                "severity": "critical",
                "vulnerable_version_range": "< 0.0.5",
                "first_patched_version": {"identifier": "0.0.5"},
            }
        ],
        "cvss": {
            "vector_string": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            "score": 10.0,
        },
        "cwes": [
            {
                "cwe_id": "CWE-77",
                "name": "Improper Neutralization of Special Elements used in a Command ('Command Injection')",
            }
        ],
    },
}
