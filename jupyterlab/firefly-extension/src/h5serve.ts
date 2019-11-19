// Copyright (c) HDFGroup.
import {
  JSONExt, JSONValue
} from '@phosphor/coreutils';


/**
 * The namespace for dealing with the H5Serve API.
 */
export
namespace H5Serve {
  /**
   * Fetch the domains which match the given arguments.
   *
   * @param args - The arguments for making the request.
   *
   * @returns A promise which yields the matching domains.
   */
  export
  async function fetchDomains(args: fetchDomains.Args): Promise<fetchDomains.Result> {
    // Unpack the arguments.
    let { endpoint, bucket, folder, query, signal } = args;

    // Set up the url.
    let url = `${endpoint}/domains`;

    // Add the bucket.
    url += `?bucket=${encodeURIComponent(bucket)}`;

    // Add the domain.
    url += `&domain=${encodeURIComponent(folder)}`;

    // Add the query if needed.
    if (query && query.length > 0) {
      url += `&query=${encodeURIComponent(query.map(clause => {
        return `${clause.attribute} ${clause.op} ${clause.value}`;
      }).join(' AND '))}`;
    }

    // Set up the request init object.
    let headers: HeadersInit = { Connection: 'Keep-Alive' };
    let init: RequestInit = { headers, signal: signal || null };

    // Fetch the URL.
    let response = await fetch(url, init);

    // Grab the response JSON.
    let json: JSONValue = await response.json();

    // Validate the root object.
    if (!JSONExt.isObject(json)) {
      throw new Error('invalid query response');
    }

    // Validate the domains array.
    if (!JSONExt.isArray(json.domains)) {
      throw new Error('invalid query response');
    }

    // Validate each domain item.
    for (let domain of json.domains) {
      if (!JSONExt.isObject(domain) ||
          typeof domain.root !== 'string' ||
          typeof domain.class !== 'string' ||
          typeof domain.owner !== 'string' ||
          typeof domain.created !== 'number' ||
          typeof domain.lastModified !== 'number' ||
          typeof domain.name !== 'string') {
        throw new Error('invalid domain response');
      }
    }

    // Return the validated domains.
    return json.domains as fetchDomains.Result;
  }

  /**
   * The namespace for the `fetchDomains` function statics.
   */
  export
  namespace fetchDomains {
    /**
     * A type alias for the supported operators.
     */
    export
    type Operator = '==' | '<=' | '>=' | '<' | '>' ;

    /**
     * An array of the supported operators.
     */
    export
    const operators: ReadonlyArray<Operator> = [
      '==', '<=', '>=', '<', '>'
    ];

    /**
     * A single clause in an query.
     */
    export
    type Clause = {
      /**
       * The attribute name of interest.
       */
      readonly attribute: string;

      /**
       * The relevant operator.
       */
      readonly op: Operator;

      /**
       * The value for the clause.
       */
      readonly value: string;
    };

    /**
     * A type alias for a query.
     */
    export
    type Query = ReadonlyArray<Clause>;

    /**
     * The arguments for the `fetchDomains` function.
     */
    export
    type Args = {
      /**
       * The URL endpoint for the fetch.
       *
       * Example: `'https://hsdshdflab.hdfgroup.org'`
       */
      readonly endpoint: string;

      /**
       * The bucket for the fetch.
       *
       * Example: `'firefly-hsds'`
       */
      readonly bucket: string;

      /**
       * The root folder which contains the relevant child domains.
       *
       * Example: `'/FIREfly/h5/'`
       */
      readonly folder: string;

      /**
       * An optional query to apply to the data.
       */
      readonly query?: Query;

      /**
       * An optional signal to abort the fetch.
       */
      readonly signal?: AbortSignal;
    };

    /**
     * A result item for the `fetchDomains` function.
     */
    export
    type Domain = {
      root: string;
      class: string;
      owner: string;
      created: number;
      lastModified: number;
      name: string;
    };

    /**
     * The result of the `fetchDomains` function.
     */
    export
    type Result = Domain[];
  }

  /**
   * Fetch the attributes for a particular domain.
   *
   * @param args - The arguments for the fetch.
   *
   * @returns A promise which yields the attributes.
   */
  export
  async function fetchDomainAttributes(args: fetchDomainAttributes.Args): Promise<fetchDomainAttributes.Result> {
    // Unpack the arguments.
    let { endpoint, bucket, root, domain, signal } = args;

    // Set up the url.
    let url = `${endpoint}/groups/${root}`;

    // Add the bucket.
    url += `?bucket=${encodeURIComponent(bucket)}`;

    // Add the domain.
    url += `&domain=${encodeURIComponent(domain)}`;

    // Add the attribtues.
    url += `&include_attrs=1`;

    // Set up the request init object.
    let headers: HeadersInit = { Connection: 'Keep-Alive' };
    let init: RequestInit = { headers, signal: signal || null };

    // Fetch the URL.
    let response = await fetch(url, init);

    // Grab the response JSON.
    let json: JSONValue = await response.json();

    // Validate the JSON response.
    if (!JSONExt.isObject(json)) {
      throw new Error('invalid response');
    }

    // Validate the attributes response.
    if (!JSONExt.isObject(json.attributes)) {
      throw new Error('invalid response');
    }

    // TODO - better validation on these attributes.
    return json.attributes as fetchDomainAttributes.Result;
  }

  /**
   * The namespace for the `fetchDomainAttributes` function.
   */
  export
  namespace fetchDomainAttributes {
    /**
     * The arguments for the `fetchDomainAttributes` function.
     */
    export
    type Args = {
      /**
       * The URL endpoint for the fetch.
       *
       * Example: `'https://hsdshdflab.hdfgroup.org'`
       */
      readonly endpoint: string;

      /**
       * The bucket for the fetch.
       *
       * Example: `'firefly-hsds'`
       */
      readonly bucket: string;

      /**
       * The unique id of the root group.
       *
       * Example: `'g-84264c92-bd7a4a83-0cae-c41a35-f2c20b'`
       */
      readonly root: string;

      /**
       * The full path to the relevant domain.
       *
       * Example: `'/FIREfly/h5/A10-ED000001-201712160409.h5'`
       */
      readonly domain: string;

      /**
       * An optional signal to abort the fetch.
       */
      readonly signal?: AbortSignal;
    };

    /**
     * A type alias for a domain attribute.
     */
    export
    type Attribute = {
      type: {
        class: string,
        length: string,
        charSet: string,
        strPad: string
      },
      shape: {
        class: string
      },
      value: JSONValue;
      created: number;
    };

    /**
     * The result of the `fetchDomainAttributes` function.
     */
    export
    type Result = { [name: string]: Attribute };
  }
}
