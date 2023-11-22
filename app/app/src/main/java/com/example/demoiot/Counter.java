package com.example.demoiot;

public class Counter {
    private final int n;
    private int currentCnt;

    public Counter(int n) {
        this.n = n;
        this.currentCnt = n;
    }

    public boolean update() {
        this.currentCnt -= 1;
        if (this.currentCnt <= 0) {
            this.currentCnt = this.n;
            return true;
        }
        return false;
    }

    public void reset(){
        this.currentCnt = this.n;
    }
}
