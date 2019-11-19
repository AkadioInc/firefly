// Copyright (c) HDFGroup.
import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  IMainMenu
} from '@jupyterlab/mainmenu';

import {
  ReadonlyJSONObject
} from '@phosphor/coreutils';

import {
  Menu
} from '@phosphor/widgets';

import {
  Browser
} from './browser';


/**
 * The namespace for holding the extension command IDs.
 */
namespace Commands {
  /**
   * Open the FIREfly browser tab.
   */
  export
  const OPEN = 'firefly-extension:openBrowser';
}


/**
 * The plugin activation function.
 */
function activate(app: JupyterFrontEnd, mainMenu: IMainMenu): void {
  // Create the domain browser.
  const browser = new Browser({
    endpoint: 'https://hsdshdflab.hdfgroup.org',
    bucket: 'firefly-hsds',
    folder: '/FIREfly/h5/'
  });

  // Set the query panel icon and title.
  browser.id = 'firefly-Browser';
  browser.title.closable = true;
  browser.title.label = 'FIREfly Browser';
  browser.title.iconClass = 'firefly-Browser-icon fa fa-fire';

  // Add the open command.
  app.commands.addCommand(Commands.OPEN, {
    label: 'FIREfly Browser',
    execute: openBrowser
  });

  // Create an `'Experimental'` menu for opening the FIREfly browser.
  let menu = new Menu({ commands: app.commands });
  menu.title.label = 'Experimental';
  menu.addItem({ command: Commands.OPEN });

  // Add the experimental menu to the main menu bar.
  mainMenu.addMenu(menu, { rank: 1000 });

  // The command execution function to open the browser.
  function openBrowser(args: ReadonlyJSONObject): void {
    if (!app.shell.contains(browser)) {
      app.shell.add(browser, 'main');
      browser.activate();
    }
  }
}


/**
 * The FIREfly plugin definition.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'firefly-extension:plugin',
  requires: [IMainMenu],
  autoStart: true,
  activate: activate
};


export default plugin;
