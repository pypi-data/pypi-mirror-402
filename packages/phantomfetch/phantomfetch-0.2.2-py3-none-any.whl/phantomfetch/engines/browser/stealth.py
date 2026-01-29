"""
Stealth scripts for evading bot detection.
"""


def get_stealth_scripts() -> list[str]:
    """
    Return a list of JavaScript scripts to inject for evasion.
    """
    return [
        # 1. Strip navigator.webdriver
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """,
        # 2. Mock window.chrome
        """
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {
                isInstalled: false,
                getDetails: function() {},
                getIsInstalled: function() {},
                runningState: function() {}
            }
        };
        """,
        # 3. Mock navigator.permissions
        """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: 'prompt', onchange: null }) :
            originalQuery(parameters)
        );
        """,
        # 4. Mock navigator.plugins
        """
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    {
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format'
                    },
                    {
                        name: 'Chrome PDF Viewer',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: 'Portable Document Format'
                    },
                    {
                        name: 'Native Client',
                        filename: 'internal-nacl-plugin',
                        description: 'Native Client Executable'
                    }
                ];
                // Behave like a real PluginArray
                plugins.item = (i) => plugins[i];
                plugins.namedItem = (name) => plugins.find(p => p.name === name);
                return plugins;
            }
        });
        """,
        # 5. Mock navigator.languages (ensure consistency)
        """
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        """,
    ]
