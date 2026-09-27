/**
 * CircularBuffer implementation in Node.js
 * Supports overwriting oldest data when full.
 */
export class CircularBuffer<T> {

    private buffer: Array<T | undefined>;
    private capacity: number;
    private head: number;
    private tail: number;
    private size: number;

    /**
     * @param {number} capacity - Maximum number of elements the buffer can hold
     */
    constructor(capacity: number) {
        this.capacity = capacity;
        this.buffer = new Array<T>(capacity);
        this.head = 0;
        this.tail = 0;
        this.size = 0;
    }

    /**
     * Adds an element to the buffer (overwrites oldest if full)
     * @param {*} item - Element to store
     */
    push(item: T) {
        this.buffer[this.head] = item;
        this.head = (this.head + 1) % this.capacity;

        if (this.size < this.capacity) {
            this.size++;
        } else {
            // Buffer full, move tail forward (overwrite oldest)
            this.tail = (this.tail + 1) % this.capacity;
        }
    }

    /**
     * Removes and returns the oldest element from the buffer
     * @returns {*} Oldest element or null if empty
     */
    pop() {
        if (this.isEmpty()) return null;
        const item = this.buffer[this.tail];
        this.buffer[this.tail] = undefined; // Optional: clear reference
        this.tail = (this.tail + 1) % this.capacity;
        this.size--;
        return item;
    }

    /**
     * Returns the oldest element without removing it
     * @returns {*} Oldest element or null if empty
     */
    peek() {
        return this.isEmpty() ? null : this.buffer[this.tail];
    }

    /**
     * Adds an element to the buffer (overwrites oldest if full)
     * @param {*} items - Elements to store
     */
    fill(items: T[]) {
        if (items.length > this.capacity) {
            // If more items than capacity, keep only the last 'capacity' items
            throw new Error(`Too many items to fill: ${items.length} exceeds capacity ${this.capacity}`);
        }

        this.buffer = new Array<T>(this.capacity);
        this.buffer.push(...items);
    }

    /**
     * Checks if the buffer is empty
     * @returns {boolean}
     */
    isEmpty() {
        return this.size === 0;
    }

    /**
     * Checks if the buffer is full
     * @returns {boolean}
     */
    isFull() {
        return this.size === this.capacity;
    }

    /**
     * Returns the current number of elements
     * @returns {number}
     */
    length() {
        return this.size;
    }

    /**
     * Returns a snapshot array of the buffer contents (oldest to newest)
     * @returns {Array}
     */
    toArray() {
        const result = [];
        for (let i = 0; i < this.size; i++) {
            result.push(this.buffer[(this.tail + i) % this.capacity]);
        }
        return result;
    }
}