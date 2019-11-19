// Copyright (c) HDFGroup.
import {
  DataModel
} from './vendor/phosphor/datagrid';

import {
  BrowserModel
} from './browsermodel';


/**
 * A grid data model implementation for FIREfly browser data.
 */
export
class BrowserGridModel extends DataModel {
  /**
   * Construct a new browser grid model.
   *
   * @params options - The options for initializing the grid model.
   */
  constructor(options: BrowserGridModel.IOptions) {
    super();
    this.model = options.model;
    this.model.dataChanged.connect(this._onDataChanged, this);
  }

  /**
   * The domain browser model which contains the data.
   */
  readonly model: BrowserModel;

  /**
   * Get the row count for the specified row region.
   */
  rowCount(region: DataModel.RowRegion): number {
    if (region === 'column-header') {
      return 1;
    }
    return this.model.data.length;
  }

  /**
   * Get the column count for the specified column region.
   */
  columnCount(region: DataModel.ColumnRegion): number {
    if (region === 'row-header') {
      return 0;
    }
    return Private.attributes.length;
  }

  /**
   * Get the data value for the specified cell region.
   */
  data(region: DataModel.CellRegion, row: number, col: number): any {
    if (region === 'body') {
      let attr = Private.attributes[col];
      return this.model.data[row][attr] || null;
    }
    if (region === 'column-header') {
      return Private.attributes[col];
    }
    return null;
  }

  /**
   * A signal handler invoked on the model `dataChanged` signal.
   */
  private _onDataChanged(model: unknown, index: number): void {
    if (index < 0) {
      this.emitChanged({
        type: 'model-reset'
      });
    } else {
      this.emitChanged({
        type: 'cells-changed',
        region: 'body',
        row: index,
        rowSpan: 1,
        column: 0,
        columnSpan: this.columnCount('body')
      });
    }
  }
}


/**
 * The namespace for the `BrowserGridModel` class statics.
 */
export
namespace BrowserGridModel {
  /**
   * An options object for initializing the browser grid model.
   */
  export
  interface IOptions {
    /**
     * The domain browser model of interest.
     */
    model: BrowserModel;
  }
}


/**
 * The namespace for the module implementation details.
 */
namespace Private {
  /**
   * The attributes to be shown in the grid.
   *
   * TODO - Ideally these would be dynamically discovered.
   */
  export
  const attributes = BrowserModel.domainAttributes.filter(attr => {
    return attr !== 'root';
  });
}
