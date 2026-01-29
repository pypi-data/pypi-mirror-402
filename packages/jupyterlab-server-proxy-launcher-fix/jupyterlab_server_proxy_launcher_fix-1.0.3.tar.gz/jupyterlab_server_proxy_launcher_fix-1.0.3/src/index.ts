import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { LabIcon } from '@jupyterlab/ui-components';
import {
  fetchServersInfo,
  isKernelCategory,
  IServerProcess
} from './serverInfo';
import { fetchSvgIcon, createTextIcon } from './iconUtils';

const iconCache = new Map<string, LabIcon>();

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_server_proxy_launcher_fix:plugin',
  description: 'Fixes SVG icon display for jupyter-server-proxy launchers',
  autoStart: true,
  activate: async (app: JupyterFrontEnd): Promise<void> => {
    console.log(
      'JupyterLab extension jupyterlab_server_proxy_launcher_fix is activated!'
    );

    try {
      const serversInfo = await fetchServersInfo();
      const serverProcesses = serversInfo.server_processes || [];

      console.log(
        '[server-proxy-launcher-fix] Found servers:',
        serverProcesses.map((sp: IServerProcess) => sp.name)
      );

      // Pre-fetch and cache icons for non-kernel categories
      for (const sp of serverProcesses) {
        if (!sp.launcher_entry.enabled) {
          continue;
        }
        const category = sp.launcher_entry.category || 'Other';
        if (isKernelCategory(category)) {
          continue;
        }

        console.log(
          `[server-proxy-launcher-fix] Caching icon for "${sp.name}"`
        );

        const iconName = `server-proxy-launcher-fix:${sp.name}`;
        let icon = sp.launcher_entry.icon_url
          ? await fetchSvgIcon(sp.launcher_entry.icon_url, iconName)
          : null;

        if (!icon) {
          icon = createTextIcon(iconName, sp.launcher_entry.title);
        }

        // Cache by title - matches args.title in server-proxy:open calls
        // server-proxy appends " [↗]" suffix when new_browser_tab is true
        const title = sp.launcher_entry.title;
        iconCache.set(title, icon);
        if (sp.new_browser_tab) {
          iconCache.set(`${title} [↗]`, icon);
        }
      }

      console.log(
        '[server-proxy-launcher-fix] Icon cache:',
        Array.from(iconCache.keys())
      );

      // Wrap commands.icon() to return cached icons for server-proxy:open
      const originalIcon = app.commands.icon.bind(app.commands);
      (app.commands as any).icon = (id: string, args: any = {}) => {
        if (
          id === 'server-proxy:open' &&
          args.title &&
          iconCache.has(args.title)
        ) {
          console.log(
            `[server-proxy-launcher-fix] Returning icon for "${args.title}"`
          );
          return iconCache.get(args.title);
        }
        return originalIcon(id, args);
      };

      console.log('[server-proxy-launcher-fix] Wrapped commands.icon()');
    } catch (error) {
      console.warn('[server-proxy-launcher-fix] Failed to initialize:', error);
    }
  }
};

export default plugin;
