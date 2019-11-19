// Copyright (c) HDFGroup.
import {
  Toolbar
} from '@jupyterlab/apputils';

import {
  PanelLayout, SplitPanel, Widget
} from '@phosphor/widgets'

import {
  BrowserGrid
} from './browsergrid';

import {
  BrowserModel
} from './browsermodel';

import {
  QueryPanel
} from './querypanel';


/**
 * A widget which implements the FIREfly browser.
 */
export
class Browser extends Widget {
  /**
   * Construct a new FIREfly browser.
   *
   * @param options - The options for initializing the browser.
   */
  constructor(options: Browser.IOptions) {
    super();
    this.addClass('firefly-Browser');

    // Create the browser model.
    let browserModel = new BrowserModel(options);

    // Create the internal widgets.
    let queryPanel = new QueryPanel({ model: browserModel });
    let browserGrid = new BrowserGrid({ model: browserModel });

    // Save a reference to the query panel for activation requests.
    this._queryPanel = queryPanel;

    // Set the widget stretch factors.
    SplitPanel.setStretch(queryPanel, 0);
    SplitPanel.setStretch(browserGrid, 1);

    // Populate the splitter.
    let splitter = new SplitPanel({ orientation: 'horizontal', spacing: 1 });
    splitter.addWidget(queryPanel);
    splitter.addWidget(browserGrid);
    splitter.setRelativeSizes([0, 1]); // https://github.com/phosphorjs/phosphor/issues/442

    // Set up the layout.
    let layout = new PanelLayout();
    layout.addWidget(new Toolbar());
    layout.addWidget(splitter);

    // Install the layout on the widget.
    this.layout = layout;
  }

  /**
   * A message handler invoked on an `'activate-request'` message.
   */
  protected onActivateRequest(): void {
    this._queryPanel.activate();
  }

  private _queryPanel: QueryPanel;
}


/**
 * The namespace for the `Browser` class statics.
 */
export
namespace Browser {
  /**
   * The options for initializing a domain browser.
   */
  export
  interface IOptions extends BrowserModel.IOptions { }
}
