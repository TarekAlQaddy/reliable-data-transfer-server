import java.io.IOException;

public class Main {
    public static void main(String[] args) throws IOException {
        if(args.length == 0){
            System.out.println("Usage: Main.java option\n\toption:\n-st:\t Stop and Wait\n-sr:\tSelective Repeat\n-go:\tGo Back N");
            return;
        }
        switch (args[0]) {
            case "-st":
                StopAndWait method1 = new StopAndWait("client.in");
                break;
            case "-sr":
                SelectiveRepeat method2 = new SelectiveRepeat("client.in");
                break;
            case "-go":
                GoBackN method3 = new GoBackN("client.in");
                break;
            default:

        }
    }
}
