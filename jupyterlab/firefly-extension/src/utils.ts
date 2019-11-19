// Copyright (c) HDFGroup.


/**
 * The namespace for the miscellaneous package utilities.
 */
export
namespace Utils {
  /**
   * The batch size for asyc map operations.
   *
   * TODO - Should this be globally configurable?
   */
  const BATCH_SIZE = 50;

  /**
   * Apply an async function across arbitrary data.
   *
   * @param fn - The function to apply to the data.
   *
   * @param data - The data of interest.
   *
   * @param onvalue - The callback invoked for a resolved value.
   *
   * @param onerror - The callback invoked for each error encountered.
   *
   * @returns A promise which resolves when the operation is completed.
   *
   * #### Notes
   * This is useful for issuing multiple parallel network requests.
   */
  export
  async function asyncApply<T, U>(fn: (item: T) => Promise<U>, data: ReadonlyArray<T>, onvalue: (index: number, value: U) => void, onerror: (index: number, error: any) => void): Promise<void> {
    // Set up the index variable.
    let index = 0;

    // Set up the initial batch.
    let batch: Promise<void>[] = [];

    // Fire the batch.
    for (let i = 0, n = Math.min(BATCH_SIZE, data.length); i < n; ++i) {
      batch.push(applyNext());
    }

    // Wait for the batch to complete.
    await Promise.all(batch);

    function applyNext(): Promise<void> {
      // Grab the index to be processed.
      let i = index++;

      // Bail if there is nothing left to process.
      if (i >= data.length) {
        return Promise.resolve(undefined);
      }

      // Invoke the async function.
      let promise1 = fn(data[i]);

      // Invoke the result handler.
      let promise2 = promise1.then(result => { onvalue(i, result); });

      // Handle errors in the chain.
      let promise3 = promise2.catch(error => { onerror(i, error) });

      // Finally, apply the function to the next value.
      return promise3.then(applyNext);
    }
  }
}
