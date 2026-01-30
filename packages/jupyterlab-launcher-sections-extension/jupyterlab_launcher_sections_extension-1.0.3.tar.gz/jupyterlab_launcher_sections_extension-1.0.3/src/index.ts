import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';
import { IConfigResponse } from './types';
import { LauncherSectionApplier } from './applier';

/**
 * Initialization data for the jupyterlab_launcher_sections_extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_launcher_sections_extension:plugin',
  description:
    'Jupyterlab extension to allow setting section-specific icons for the launcher',
  autoStart: true,
  activate: async (app: JupyterFrontEnd) => {
    console.log(
      'JupyterLab extension jupyterlab_launcher_sections_extension is activated!'
    );
    const applier = new LauncherSectionApplier();

    try {
      const config = await requestAPI<IConfigResponse>('config');
      applier.setConfigs(config.sections);
    } catch (reason) {
      console.error(
        `[LauncherSectionIcons] Failed to load configurations: ${reason}`
      );
      return;
    }

    // Start applying icons after the app is restored
    app.restored.then(() => {
      applier.start();
    });
  }
};

export default plugin;
