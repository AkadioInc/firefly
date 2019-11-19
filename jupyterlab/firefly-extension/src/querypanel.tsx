// Copyright (c) HDFGroup.
import {
  Message
} from '@phosphor/messaging';

import {
  Widget
} from '@phosphor/widgets';

import {
  VDOM
} from './vendor/phosphor/vdom';

import {
  BrowserModel
} from './browsermodel';


/**
 * A widget which displays the query portion of a `BrowserModel`.
 */
export
class QueryPanel extends Widget {
  /**
   * Construct a new query panel widget.
   *
   * @param options - The options for initializing the widget.
   */
  constructor(options: QueryPanel.IOptions) {
    super();
    this.addClass('firefly-QueryPanel');
    this.setFlag(Widget.Flag.DisallowLayout);
    this.model = options.model;
  }

  /**
   * The browser model which drives the widget.
   */
  readonly model: BrowserModel;

  /**
   * A message handler invoked on an `'before-attach'` message.
   */
  protected onBeforeAttach(msg: Message): void {
    this.model.queryChanged.connect(this._onQueryChanged, this);
    this.update();
  }

  /**
   * A message handler invoked on an `'after-detach'` message.
   */
  protected onAfterDetach(msg: Message): void {
    this.model.queryChanged.disconnect(this._onQueryChanged, this);
  }

  /**
   * A message handler invoked on an `'activate-request'` message.
   */
  protected onActivateRequest(): void {
    // Bail early if the panel already has focus.
    if (this.node.contains(document.activeElement)) {
      return;
    }

    // Bail early if the content has not been rendered.
    if (!this._dummyInputRef.current) {
      return;
    }

    // Focus the dummy input.
    (this._dummyInputRef.current as HTMLInputElement).focus();
  }

  /**
   * A message handler inovked on an `'update-request'` message.
   */
  protected onUpdateRequest(msg: Message): void {
    VDOM.render(this._render(), this.node);
    this._maybeFocusLastInput();
  }

  /**
   * A signal handler invoked on the model `changed` signal.
   */
  private _onQueryChanged(): void {
    this.update();
  }

  /**
   * Render the content for the panel.
   */
  private _render() {
    return [this._renderQuerySection()];
  }

  /**
   * Render the query section for the panel.
   */
  private _renderQuerySection() {
    return(
      <section class='firefly-QueryPanel-query'>
        <datalist id='firefly-QueryPanel-queryAttrList'>
          {this._renderAttrOptions()}
        </datalist>
        <header>
          <span>Query</span>
          <button
            class='fa fa-refresh'
            title='Refresh'
            onclick={this._onRefreshClick} />
        </header>
        <p>{this._renderQueryTable()}</p>
      </section>
    );
  }

  /**
   * Render the query table for the panel.
   */
  private _renderQueryTable() {
    return (
      <table>
        <thead>
          <th>Query Attribute</th>
          <th></th>
          <th>Value</th>
          <th></th>
        </thead>
        <tbody>
          {this.model.query.map(item => this._renderQueryItem(item))}
        </tbody>
        <tfoot>
          <td colspan={4}>
            <input
              ref={this._dummyInputRef}
              data-type='dummy'
              placeholder='Add Attribute'
              onkeypress={this._onDummyKeypress} />
          </td>
        </tfoot>
      </table>
    );
  }

  /**
   * Render the attribute options for the query table.
   */
  private _renderAttrOptions() {
    return BrowserModel.knownAttributes.map(attr => (
      <option>{attr}</option>
    ));
  }

  /**
   * Render the operator options for the given query item.
   */
  private _renderOpOptions(item: BrowserModel.QueryItem) {
    return BrowserModel.operators.map(op => (
      <option selected={item.op === op}>{op}</option>
    ));
  }

  /**
   * Render the table row for the given query item.
   */
  private _renderQueryItem(item: BrowserModel.QueryItem) {
    let lastItem = this.model.query[this.model.query.length - 1];
    let ref = item === lastItem ? this._lastInputRef : undefined;
    return (
      <tr>
        <td>
          <input
            ref={ref}
            list='firefly-QueryPanel-queryAttrList'
            data-type='attr'
            data-item={item.id}
            value={item.attribute}
            oninput={this._onAttrInput} />
        </td>
        <td>
          <select data-item={item.id} onchange={this._onOpChange}>
            {this._renderOpOptions(item)}
          </select>
        </td>
        <td>
          <input
            type={Private.inputTypeForAttr(item.attribute)}
            placeholder={Private.placeholderForAttr(item.attribute)}
            step='any'
            data-type='value'
            data-item={item.id}
            value={Private.unquote(item.value)}
            oninput={this._onValueInput} />
        </td>
        <td>
          <button
            class='fa fa-trash'
            title='Delete Item'
            data-item={item.id}
            onclick={this._onTrashClick} />
        </td>
      </tr>
    );
  }

  /**
   * Redirect the focus to the last input field, if needed.
   */
  private _maybeFocusLastInput(): void {
    // Deref the dummy and last input refs.
    let dummyInput = this._dummyInputRef.current;
    let lastInput = this._lastInputRef.current;

    // Bail early if either of the refs are invalid.
    if (!dummyInput || !lastInput) {
      return;
    }

    // Bail early if the dummy input is not focused.
    if (dummyInput !== document.activeElement) {
      return;
    }

    // Cast the last input to an input element.
    let input = lastInput as HTMLInputElement;

    // Focus the input field.
    input.focus();

    // Move the cursor to the last position.
    let n = input.value.length;
    input.setSelectionRange(n, n);
  }

  /**
   * Handle the dummy input `'keypress'` event.
   */
  private _onDummyKeypress = (event: Event) => {
    event.preventDefault();
    event.stopPropagation();
    let attribute = (event as KeyboardEvent).key;
    this.model.addQueryItem({ attribute, op: '==', value: '' });
  };

  /**
   * Handle the attribute field `'input'` event.
   */
  private _onAttrInput = (event: Event) => {
    let input = event.target as HTMLInputElement;
    let id = Number(input.dataset['item']);
    this.model.editQueryItem(id, { attribute: input.value });
  };

  /**
   * Handle the value field `'input'` event.
   */
  private _onValueInput = (event: Event) => {
    let input = event.target as HTMLInputElement;
    let id = Number(input.dataset['item']);
    let value = Private.quote(input.value);
    this.model.editQueryItem(id, { value });
  };

  /**
   * Handle the operator select `'change'` event.
   */
  private _onOpChange = (event: Event) => {
    let select = event.target as HTMLSelectElement;
    let id = Number(select.dataset['item']);
    let op = select.value as BrowserModel.Operator;
    this.model.editQueryItem(id, { op });
  };

  /**
   * Handle the trash button `'click'` event.
   */
  private _onTrashClick = (event: Event) => {
    let button = event.target as HTMLButtonElement;
    let id = Number(button.dataset['item']);
    this.model.removeQueryItem(id);
  };

  /**
   * Handle the refresh button `'click'` event.
   */
  private _onRefreshClick = (event: Event) => {
    this.addClass('hdfg-mod-loading');
    this.model.fetch().then(() => {
      this.removeClass('hdfg-mod-loading');
    }).catch(error => {
      this.removeClass('hdfg-mod-loading');
      throw error;
    });
  };

  private _lastInputRef: VDOM.JSX.Ref = {};
  private _dummyInputRef: VDOM.JSX.Ref = {};
}


/**
 * The namespace for the `QueryPanel` class statics.
 */
export
namespace QueryPanel {
  /**
   * An options object for initializing a query panel.
   */
  export
  interface IOptions {
    /**
     * The query model which drives the widget.
     */
    model: BrowserModel;
  }
}


/**
 * The namespace for the module implementation details.
 */
namespace Private {
  /**
   * Get the input field type for a queryable attribute.
   *
   * TODO - update server API so these attributes don't need to be
   * hard-coded.
   */
  export
  function inputTypeForAttr(attr: string): 'text' | 'number' | 'date' {
    switch (attr) {
    case 'date_created':
    case 'date_metadata_modified':
    case 'date_modified':
    case 'time_coverage_end':
    case 'time_coverage_start':
      return 'date';
    case 'max_altitude':
    case 'max_gforce':
    case 'max_lat':
    case 'max_lon':
    case 'max_pitch':
    case 'max_roll':
    case 'max_speed':
    case 'min_altitude':
    case 'min_gforce':
    case 'min_lat':
    case 'min_lon':
    case 'min_pitch':
    case 'min_roll':
    case 'min_speed':
      return 'number';
    default:
      return 'text';
    }
  }

  /**
   * Get the input field placeholder for a queryable attribute.
   */
  export
  function placeholderForAttr(attr: string): string {
    return inputTypeForAttr(attr);
  }

  /**
   * Quote the value for an attribute if needed.
   */
  export
  function quote(value: string): string {
    return isNaN(Number(value)) ? `"${value}"` : value;
  }

  /**
   * Unquote the value for an attribute if needed.
   */
  export
  function unquote(value: string): string {
    return value[0] === '"' ? value.slice(1, value.length - 1) : value;
  }
}
