import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Launcher entry configuration from jupyter-server-proxy
 */
export interface ILauncherEntry {
  enabled: boolean;
  title: string;
  path_info: string;
  icon_url?: string;
  category?: string;
}

/**
 * Server process configuration from jupyter-server-proxy
 */
export interface IServerProcess {
  name: string;
  new_browser_tab: boolean;
  launcher_entry: ILauncherEntry;
}

/**
 * Response from /server-proxy/servers-info endpoint
 */
export interface IServersInfo {
  server_processes: IServerProcess[];
}

/**
 * Categories that JupyterLab treats as "kernel" categories.
 * These render kernelIconUrl correctly, so we don't need to fix them.
 */
const KERNEL_CATEGORIES = ['Notebook', 'Console'];

/**
 * Check if a category is a kernel category (Notebook or Console)
 */
export function isKernelCategory(category: string | undefined): boolean {
  return category !== undefined && KERNEL_CATEGORIES.includes(category);
}

/**
 * Fetch server proxy configuration from the jupyter-server-proxy endpoint
 */
export async function fetchServersInfo(): Promise<IServersInfo> {
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(settings.baseUrl, 'server-proxy/servers-info');

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, {}, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error as Error);
  }

  if (!response.ok) {
    // 404 means jupyter-server-proxy is not installed - return empty list
    if (response.status === 404) {
      return { server_processes: [] };
    }
    throw new ServerConnection.ResponseError(response);
  }

  const data = await response.json();
  return data as IServersInfo;
}
