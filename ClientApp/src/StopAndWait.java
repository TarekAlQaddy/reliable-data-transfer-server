import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.nio.charset.Charset;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Random;

public class StopAndWait {

    private static File file= new File("client.in");
    private static BufferedReader reader;

    private static String[] inputFile = new String[5];

    private static final int BYTE_SIZE = 200;
    private static ArrayList<Packet> recievedPackets = new ArrayList<>();
    private static DatagramSocket socket;
    private static InetAddress address;


    public StopAndWait(String filename) throws IOException {
        Instant start = Instant.now();
        reader = new BufferedReader(new FileReader(filename));
        int i = 0;
        String text;
        while ((text = reader.readLine()) != null){
            inputFile [i] = text;
            i++;
        }

        address = InetAddress.getByName(inputFile[0]);
        int serverPort = Integer.parseInt(inputFile[1]);
        socket = new DatagramSocket(Integer.parseInt(inputFile[2]));
        String fileName = inputFile[3];
        /*  a packet consists of : [checksum,seq_no,is_last_packet, is_ack]*/
        String s = "2&0&0&0&$" + fileName;
        DatagramPacket initialRequest = new DatagramPacket(s.getBytes(), s.length(), address, serverPort);
//        socket.setSoTimeout(1000);
        socket.send(initialRequest);

        try {
            /*recieving ack*/
            DatagramPacket serverFirstAck = new DatagramPacket(new byte[BYTE_SIZE],BYTE_SIZE);
            System.out.println("abl el recieve");
            socket.receive(serverFirstAck);
            System.out.println("b3d el recieve");
//            System.out.println(Arrays.toString(serverFirstAck.getData()));
            String serverFirstAckData = new String(serverFirstAck.getData());
            String[] splittedServerFirstAckData = serverFirstAckData.split("&&");
            splittedServerFirstAckData = splittedServerFirstAckData[0].split("&");
//            for(int i = 0;i < splittedServerFirstAckData.length;i++){
//                System.out.println(splittedServerFirstAckData[i]);
//            }
//            double random = 0 + Math.random() * (1 - 0);
//            if(random < 0.5){
//                Packet packet = Utils.corruptPacket(serverFirstAckData);
//            }
            Packet packet = assignToPacket(splittedServerFirstAckData,0);
            System.out.println(packet.getChecksum());
            if(packet.isIs_ack()){
                while (true){
                    try {
                        DatagramPacket serverData = new DatagramPacket(new byte[BYTE_SIZE],BYTE_SIZE);
                        socket.receive(serverData);
                        String packetOfData = new String(serverData.getData());
                        String[] recievedPacket = packetOfData.split("&");
                        Packet dataPacket = assignToPacket(recievedPacket,1);
//                        if(x == dataPacket.getChecksum())
//                            System.out.println(computeChecksum(packetOfData.substring(3)));

                        if (recievedPackets.size() == 0) {
                            int temp = computeChecksum(packetOfData.substring(3));
                            if(temp == dataPacket.getChecksum()){
                                recievedPackets.add(dataPacket);
                                sendAck(dataPacket);
                            }else
                                continue;
                        }else {
                            if(recievedPackets.get(recievedPackets.size()-1).getSeq_no() != dataPacket.getSeq_no()){
                                int temp = computeChecksum(packetOfData.substring(3));
                                if(temp == dataPacket.getChecksum()){
                                    recievedPackets.add(dataPacket);
                                    sendAck(dataPacket);
                                }else
                                    continue;
                            }
                        }

                        System.out.println(recievedPackets.size());
                        if(dataPacket.getIsLastPacket() == 1){
                            System.out.println("file well received, closing connection...");
                            Utils.writeToFile(recievedPackets);
                            Instant end = Instant.now();
                            System.out.println(Duration.between(start, end));
                            socket.close();
                            break;
                        }
                    }catch (SocketTimeoutException e){
                        System.out.println("server isn't sending anymore, closing socket...");
                        socket.close();
                        break;
                    }
                }
            }
        }catch (SocketTimeoutException e){
            System.out.println("server didn't acknowledge, closing socket...");
            socket.close();
        }
    }

    static int computeChecksum(String packetOfData) {
        int allSum = 0;
        byte[] packet = packetOfData.getBytes(Charset.forName("UTF-8"));
        for(byte b : packet)
            allSum += b;
        int cuttedSum = allSum & 0x000000FF;
        int remaining  = allSum >> 8;
        while (remaining != 0){
            cuttedSum += (remaining & 0x000000FF);
            while ((cuttedSum & 0x0000FF00) != 0){
                int nextByte = (cuttedSum & 0x0000FF00) >> 8;
                cuttedSum &= 0x000000FF;
                cuttedSum += nextByte;
            }
            remaining = remaining >> 8;
        }

        return cuttedSum ^ 0xFF;
    }

    static Packet assignToPacket(String[] sentences,int type){
        int checksum;
        checksum = Integer.parseInt(sentences[0]);
        int seq_no = Integer.parseInt(sentences[1]);
        int is_last_packet = Integer.parseInt(sentences[2]);
        boolean is_ack = false;
        if(sentences[3].equals("1")){
            is_ack = true;
        }
        if(type == 0){
            return new Packet(checksum, seq_no, is_last_packet,is_ack);
        }else {
            String data = sentences[sentences.length-1].replace("$","");
//            String decryptedData = Utils.decrypt(data,"g");
            return new Packet(checksum, seq_no, is_last_packet,is_ack,data);
        }
    }

    private static void sendAck(Packet dataPacket) throws IOException {
        String temp = String.format("%02d",dataPacket.getSeq_no());
        String dataPacketAck = "&" + temp + "&" + dataPacket.getIsLastPacket() + "&" + "1&$";
        int computedChecksum = StopAndWait.computeChecksum(dataPacketAck);
        String formatted = String.format("%03d", computedChecksum);
        String sendAck = formatted + dataPacketAck;
        DatagramPacket sendDataPacketAck = new DatagramPacket(sendAck.getBytes(), sendAck.length(), address, 12345);
        socket.send(sendDataPacketAck);
    }
}
