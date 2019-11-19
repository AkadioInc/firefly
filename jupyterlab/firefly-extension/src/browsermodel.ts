// Copyright (c) HDFGroup.
import {
  JSONObject
} from '@phosphor/coreutils';

import {
  ISignal, Signal
} from '@phosphor/signaling';

import {
  H5Serve
} from './h5serve';

import {
  Utils
} from './utils';


/**
 * A class for modeling the state of the FIREfly browser.
 */
export
class BrowserModel {
  /**
   * Construct a new browser model.
   *
   * @param options - The options for initializing the model.
   */
  constructor(options: BrowserModel.IOptions) {
    this.endpoint = options.endpoint;
    this.bucket = options.bucket;
    this.folder = options.folder;
  }

  /**
   * A signal emitted when the query changes.
   */
  get queryChanged(): ISignal<this, void> {
    return this._queryChanged;
  }

  /**
   * A signal emitted when the data changes.
   *
   * The index will be `-1` if all data has changed.
   */
  get dataChanged(): ISignal<this, number> {
    return this._dataChanged;
  }

  /**
   * The URL endpoint for the query.
   */
  readonly endpoint: string;

  /**
   * The bucket of interest.
   */
  readonly bucket: string;

  /**
   * The folder which contains the domains interest.
   */
  readonly folder: string;

  /**
   * The query for the model.
   */
  get query(): BrowserModel.Query {
    return this._query;
  }

  /**
   * The loaded data for the model.
   */
  get data(): BrowserModel.Data {
    return this._data;
  }

  /**
   * Add a new item to the query.
   *
   * @param arg - The arguments for adding the query.
   *
   * @returns The id of the new query item.
   */
  addQueryItem(args: BrowserModel.AddQueryItemArgs): void {
    // Create a new id for the item.
    let id = this._counter++;

    // Unpack the arguments.
    let { attribute, op, value } = args;

    // Add the new query item.
    this._query.push({ id, attribute, op, value });

    // Emit the changed signal.
    this._queryChanged.emit(undefined);
  }

  /**
   * Edit an existing query item.
   *
   * @param id - The id of the item to edit.
   *
   * @param args - The arguments for editing the query.
   *
   * @throws An exception if the target query item does not exist.
   */
  editQueryItem(id: number, args: BrowserModel.EditQueryItemArgs): void {
    // Find the index of the target query item.
    let i = this._query.findIndex(item => item.id === id);

    // Throw an exception if the item does not exist.
    if (i < 0) {
      throw new Error(`Item ${id} does not exist.`);
    }

    // Create the new item.
    let item: BrowserModel.QueryItem = { ...this._query[i], ...args };

    // Update the query array.
    this._query[i] = item;

    // Emit the changed signal.
    this._queryChanged.emit(undefined);
  }

  /**
   * Remove a query item from the model.
   *
   * @param id - The id of the item to remove.
   */
  removeQueryItem(id: number): void {
    // Find the index of the target query item.
    let i = this._query.findIndex(item => item.id === id);

    // Throw an exception if the item does not exist.
    if (i < 0) {
      throw new Error(`Item ${id} does not exist.`);
    }

    // Remove the item from the query.
    this._query.splice(i, 1)[0];

    // Emit the changed signal.
    this._queryChanged.emit(undefined);
  }

  /**
   * Fetch the matching domains for the current query.
   */
  async fetch(): Promise<void> {
    // Abort a load if one is already in progress.
    if (this._abortController) {
      this._abortController.abort();
      this._abortController = null;
    }

    // Set up a new abort controller.
    this._abortController = new AbortController();
    let signal = this._abortController.signal;

    // Clear the existing data.
    this._data = [];
    this._dataChanged.emit(-1);

    // Fetch the domain objects.
    let domains = await H5Serve.fetchDomains({
      endpoint: this.endpoint,
      bucket: this.bucket,
      folder: this.folder,
      query: this.query,
      signal: signal
    });

    // Update the internal data.
    this._data = domains;
    this._dataChanged.emit(-1);

    // Convert the domains into fetch arguments.
    let data = domains.map(({ root, name }) => {
      return {
        endpoint: this.endpoint,
        bucket: this.bucket,
        root: root,
        domain: name,
        signal: signal
      };
    });

    // Set up the value callback.
    let onvalue = (i: number, result: H5Serve.fetchDomainAttributes.Result) => {
      this._data[i] = { ...this._data[i], ...Private.extractAttrs(result) };
      this._dataChanged.emit(i);
    };

    // Set up the error callback.
    let onerror = (i: number, error: any) => {
      console.error(error);
    };

    // Apply the fetch function to the fetch data.
    await Utils.asyncApply(H5Serve.fetchDomainAttributes, data, onvalue, onerror);
  }

  /**
   * Abort any pending fetch operation.
   */
  abort(): void {
    if (this._abortController) {
      this._abortController.abort();
      this._abortController = null;
    }
  }

  private _counter = 0;
  private _data: BrowserModel.Domain[] = [];
  private _query: BrowserModel.QueryItem[] = [];
  private _queryChanged = new Signal<this, void>(this);
  private _dataChanged = new Signal<this, number>(this);
  private _abortController: AbortController | null = null;
}


/**
 * The namespace for the `BrowserModel` class statics.
 */
export
namespace BrowserModel {
  /**
   * An options object for initializing the query.
   */
  export
  interface IOptions {
    /**
     * The URL endpoint for the query.
     */
    endpoint: string;

    /**
     * The bucket for the query.
     */
    bucket: string;

    /**
     * The folder which contains the domains of interest.
     */
    folder: string;
  }

  /**
   * A type alias for a query operator.
   */
  export
  type Operator = H5Serve.fetchDomains.Operator;

  /**
   * The supported query operators.
   */
  export
  const operators = H5Serve.fetchDomains.operators;

  /**
   * A type alias for an item in a query.
   */
  export
  type QueryItem = {
    /**
     * The unique id of the item.
     */
    readonly id: number;

    /**
     * The attribute name for the query item.
     */
    readonly attribute: string;

    /**
     * The operator for the query item.
     */
    readonly op: Operator;

    /**
     * The value for the query item.
     */
    readonly value: string;
  };

  /**
   * A type alias for a query.
   */
  export
  type Query = ReadonlyArray<QueryItem>;

  /**
   * A type alias for the `addQueryItem` args.
   */
  export
  type AddQueryItemArgs = {
    /**
     * The attribute name for the query item.
     */
    attribute: string;

    /**
     * The operator for the query item.
     */
    op: Operator;

    /**
     * The value for the query item.
     */
    value: string;
  };

  /**
   * A type alias for the `editQueryItem` args.
   */
  export
  type EditQueryItemArgs = Partial<AddQueryItemArgs>;

  /**
   * A type alias for the known attributes.
   */
  export
  type KnownAttributes = {
    readonly aircraft_id?: string,
    readonly aircraft_type?: string,
    readonly ch10_file?: string,
    readonly ch10_file_checksum?: string,
    readonly date_created?: string,
    readonly date_metadata_modified?: string,
    readonly date_modified?: string,
    readonly landing_location?: string,
    readonly max_altitude?: number,
    readonly max_gforce?: number,
    readonly max_lat?: number,
    readonly max_lon?: number,
    readonly max_pitch?: number,
    readonly max_roll?: number,
    readonly max_speed?: number,
    readonly min_altitude?: number,
    readonly min_gforce?: number,
    readonly min_lat?: number,
    readonly min_lon?: number,
    readonly min_pitch?: number,
    readonly min_roll?: number,
    readonly min_speed?: number,
    readonly takeoff_location?: string,
    readonly time_coverage_end?: string,
    readonly time_coverage_start?: string
  };

  /**
   * An array of the known attributes names.
   *
   * TODO - These should be dynamically discovered.
   *        Preferably, via a server-supplied schema of some sort.
   */
  export
  const knownAttributes: ReadonlyArray<keyof KnownAttributes> = [
    'aircraft_id',
    'aircraft_type',
    'ch10_file',
    'ch10_file_checksum',
    'date_created',
    'date_metadata_modified',
    'date_modified',
    'landing_location',
    'max_altitude',
    'max_gforce',
    'max_lat',
    'max_lon',
    'max_pitch',
    'max_roll',
    'max_speed',
    'min_altitude',
    'min_gforce',
    'min_lat',
    'min_lon',
    'min_pitch',
    'min_roll',
    'min_speed',
    'takeoff_location',
    'time_coverage_end',
    'time_coverage_start'
  ];

  /**
   * An object which represents a domain.
   */
  export
  type Domain = {
    readonly root: string;
    readonly name: string;
  } & KnownAttributes;

  /**
   * An array of the domain attributes names.
   */
  export
  const domainAttributes: ReadonlyArray<keyof Domain> = [
    'root',
    'name',
    ...knownAttributes
  ];

  /**
   * A type alias for the query model data.
   */
  export
  type Data = ReadonlyArray<Domain>;
}


/**
 * The namespace for the module implementation details.
 */
namespace Private {
  /**
   * Convert a fetch result into key: value attr pairs.
   *
   * TODO - better typing here.
   */
  export
  function extractAttrs(attrs: H5Serve.fetchDomainAttributes.Result): JSONObject {
    let result: JSONObject = Object.create(null);
    for (let name in attrs) {
      result[name] = attrs[name].value;
    }
    return result;
  }
}
