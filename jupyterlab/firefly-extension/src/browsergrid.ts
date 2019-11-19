// Copyright (c) HDFGroup.
import {
  SingletonLayout, Widget
} from '@phosphor/widgets';

import {
  BasicKeyHandler, BasicMouseHandler, BasicSelectionModel, CellRenderer,
  DataGrid, TextRenderer
} from './vendor/phosphor/datagrid';

import {
  BrowserGridModel
} from './browsergridmodel';

import {
  BrowserModel
} from './browsermodel';


/**
 * A simple widget which wraps a data grid for the FIREfly browser.
 */
export
class BrowserGrid extends Widget {
  /**
   * Construct a new domain browser grid.
   *
   * @param options - The options for initializing the widget.
   */
  constructor(options: BrowserGrid.IOptions) {
    super();
    this.addClass('firefly-BrowserGrid');

    // Create the internal data grid.
    let grid = new DataGrid({
      style: Private.gridStyle,
      defaultSizes: Private.gridDefaultSizes
    });

    // Set the handlers and models for the grid.
    grid.keyHandler = new BasicKeyHandler();
    grid.mouseHandler = new BasicMouseHandler();
    grid.dataModel = new BrowserGridModel({ model: options.model });
    grid.selectionModel = new BasicSelectionModel({ dataModel: grid.dataModel });

    // Set up the custom header renderer.
    grid.cellRenderers.update({ 'column-header': Private.headerRenderer });

    // Set an initial size for the zeroth column.
    grid.resizeColumn('body', 0, 280);

    // Create the layout for the widget.
    let layout = new SingletonLayout();
    layout.widget = grid;

    // Install the layout on the widget.
    this.layout = layout;
  }
}


/**
 * The namespace for the `BrowserGrid` class statics.
 */
export
namespace BrowserGrid {
  /**
   * An options object for initializing a browser grid.
   */
  export
  interface IOptions {
    /**
     * The browser model which drives the grid.
     */
    model: BrowserModel;
  }
}


/**
 * The namespace for the module implementation details.
 */
namespace Private {
  /**
   * The default grid sizes.
   */
  export
  const gridDefaultSizes: DataGrid.DefaultSizes = {
    ...DataGrid.defaultSizes,
    columnWidth: 120,
    columnHeaderHeight: 30
  };

  /**
   * The grid style.
   */
  export
  const gridStyle: DataGrid.Style = {
    ...DataGrid.defaultStyle,
    headerBackgroundColor: 'white',
    cursorBorderColor: '',
    cursorFillColor: DataGrid.defaultStyle.selectionFillColor,
    selectionBorderColor: '',
  };

  /**
   * A text renderer for the grid column headers.
   */
  export
  const headerRenderer = new TextRenderer({ format: formatHeader });

  /**
   * Format the header values for the grid.
   */
  function formatHeader(config: CellRenderer.CellConfig): string {
    let parts = String(config.value).split('_');
    for (let i = 0; i < parts.length; ++i) {
      parts[i] = parts[i][0].toUpperCase() + parts[i].slice(1);
    }
    return parts.join(' ');
  }
}
