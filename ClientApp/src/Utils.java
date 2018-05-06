import javafx.scene.paint.Stop;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;

class Utils {
    static void writeToFile(ArrayList<Packet> packets) throws IOException {
        ArrayList<String> fileData = new ArrayList<>();
        for (Packet packet : packets) {
            fileData.add(packet.getData());
        }
        Path file = Paths.get("result.txt");
        Files.write(file,fileData,Charset.forName("UTF-8"));
    }

    static Packet corruptPacket(String dataPacket){
        StringBuilder temp = new StringBuilder(dataPacket);
        temp.setCharAt(13,'x');
        String temp1 = new String(temp);
        String[] splittedServerFirstAckData = temp1.split("&&");
        splittedServerFirstAckData = splittedServerFirstAckData[0].split("&");
        Packet packet = StopAndWait.assignToPacket(splittedServerFirstAckData,1);
        return packet;
    }

    static String decrypt(String text, final String key) {
        String res = "";
        text = text.toUpperCase();
        for (int i = 0, j = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c < 'A' || c > 'Z') continue;
            res += (char)((c - key.charAt(j) + 26) % 26 + 'A');
            j = ++j % key.length();
        }
        return res;
    }
}
