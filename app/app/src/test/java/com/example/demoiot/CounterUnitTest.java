package com.example.demoiot;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;


public class CounterUnitTest {
    private Counter counter;

    @Before
    public void setUp() {
        counter = new Counter(3);
    }

    @Test
    public void testUpdate() {
        assertFalse(counter.update()); // 3-1 = 2, should return false
        assertFalse(counter.update()); // 2-1 = 1, should return false
        assertTrue(counter.update());  // 1-1 = 0, should return true and reset counter to 3
        assertFalse(counter.update()); // 3-1 = 2, should return false
    }

    @Test
    public void testReset() {
        counter.update(); // 3-1 = 2
        counter.reset(); // reset counter to 3
        assertFalse(counter.update()); // 3-1 = 2, should return false
    }

}
