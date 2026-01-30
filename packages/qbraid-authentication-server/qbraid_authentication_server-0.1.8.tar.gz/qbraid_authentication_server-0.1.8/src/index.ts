import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the @qbraid/authentication-server extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@qbraid/authentication-server:plugin',
  description:
    'A JupyterLab extension. used to get the user credentials from qbraidrc file, with the support of qbraid-core module.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log(
      'JupyterLab extension @qbraid/authentication-server is activated!'
    );
  }
};

export default plugin;
