import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class SelectiveRepeat implements Runnable{

    private static File file= new File("client.in");
    private static BufferedReader reader;
    String filename;

    private static String[] inputFile = new String[5];

    private static final int BYTE_SIZE = 200;
    private static int WINDOW_SIZE;
    private static final int SEQ_NO = 9;
    private static int baseIndex = 0;
    private static int currentStartSeqNo = 0;
    private static int[] index = new int[65536];
    private static Packet[] recievedPackets = new Packet[65536];
    private static DatagramSocket socket;
    private static InetAddress address;
    private DatagramPacket datagramPacket;
    private static Lock lock = new ReentrantLock();
    static int serverPort;

    private SelectiveRepeat(DatagramPacket packet){
        datagramPacket = packet;
    }

    SelectiveRepeat(String filename) throws IOException {
        this.filename = filename;
        reader = new BufferedReader(new FileReader(filename));
        for(int i = 0;i < 65536;i++){
            index[i] = i%SEQ_NO;
        }
        int i = 0;
        String text;
        while ((text = reader.readLine()) != null){
            inputFile [i] = text;
            i++;
        }

        address = InetAddress.getByName(inputFile[0]);
        serverPort = Integer.parseInt(inputFile[1]);
        socket = new DatagramSocket(Integer.parseInt(inputFile[2]));
        String fileName = inputFile[3];
        WINDOW_SIZE = Integer.parseInt(inputFile[4]);
        /*  a packet consists of : [checksum,seq_no,is_last_packet, is_ack]*/
        String s = "2&0&0&0&$" + fileName;
        DatagramPacket initialRequest = new DatagramPacket(s.getBytes(), s.length(), address, serverPort);
//        socket.setSoTimeout(1000);
        socket.send(initialRequest);

        try {
            /*recieving ack*/
            DatagramPacket serverFirstAck = new DatagramPacket(new byte[BYTE_SIZE], BYTE_SIZE);
            System.out.println("abl el recieve");
            socket.receive(serverFirstAck);
            System.out.println("b3d el recieve");
            String serverFirstAckData = new String(serverFirstAck.getData());
            String[] splittedServerFirstAckData = serverFirstAckData.split("&&");
            splittedServerFirstAckData = splittedServerFirstAckData[0].split("&");
            //            double random = 0 + Math.random() * (1 - 0);
//            if(random < 0.5){
//                Packet packet = Utils.corruptPacket(serverFirstAckData);
//            }
            Packet packet = StopAndWait.assignToPacket(splittedServerFirstAckData, 0);
            System.out.println(packet.getChecksum());
            if (packet.isIs_ack()) {
                while (true) {
                    try {
                        DatagramPacket serverData = new DatagramPacket(new byte[BYTE_SIZE], BYTE_SIZE);
                        socket.receive(serverData);
                        Runnable r = new SelectiveRepeat(serverData);
                        new Thread(r).run();

                    } catch (SocketTimeoutException e) {
                        System.out.println("server isn't sending anymore, closing socket...");
                        socket.close();
                        break;
                    }
                }
            }
        }catch (SocketTimeoutException e){
            System.out.println("server didn't acknowledge, closing socket...");
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void sendAck(Packet dataPacket) throws IOException {
        String temp = String.format("%02d",dataPacket.getSeq_no());
        String dataPacketAck = "&" + temp + "&" + dataPacket.getIsLastPacket() + "&" + "1&$";
        int computedChecksum = StopAndWait.computeChecksum(dataPacketAck);
        String formatted = String.format("%03d", computedChecksum);
        String sendAck = formatted + dataPacketAck;
        DatagramPacket sendDataPacketAck = new DatagramPacket(sendAck.getBytes(), sendAck.length(), address,serverPort);
        socket.send(sendDataPacketAck);
    }

    @Override
    public void run() {
        String packetOfData = new String(datagramPacket.getData());
        String[] recievedPacket = packetOfData.split("&");
        Packet dataPacket = StopAndWait.assignToPacket(recievedPacket, 1);
        lock.lock();
//        System.out.println(dataPacket.getChecksum() +  ",    "+ StopAndWait.computeChecksum(packetOfData.substring(3)));
            if (StopAndWait.computeChecksum(packetOfData.substring(3)) == dataPacket.getChecksum()) {
                int flag = 0;
                lock.lock();
                for (int i = baseIndex; i < baseIndex + WINDOW_SIZE; i++) {
                    if (index[i] == dataPacket.getSeq_no()) {
                        recievedPackets[i] = dataPacket;

                        flag = 1;
                        break;
                    }
                }
                lock.unlock();
                if (flag == 1) {
                    try {
                        updateArray(dataPacket);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                } else {
                    if (baseIndex >= WINDOW_SIZE) {
                        for (int i = baseIndex - WINDOW_SIZE; i < baseIndex; i++) {
                            if (index[i] == dataPacket.getSeq_no()) {
                                try {
                                    sendAck(dataPacket);
                                } catch (IOException e) {
                                    e.printStackTrace();
                                }
                                break;
                            }
                        }
                    }
                }
                lock.lock();
                if (dataPacket.getIsLastPacket() == 1) {
                    socket.close();
                    System.out.println("file well received, closing connection...");
                    //                        Utils.writeToFile(new ArrayList<>(Arrays.asList(recievedPackets)));
                    System.exit(1);
                }
                lock.unlock();
            }
            lock.unlock();
    }

    private void updateArray(Packet dataPacket) throws IOException {
        lock.lock();
        while (recievedPackets[baseIndex] != null){
            System.out.println("advancing");
            baseIndex++;
            currentStartSeqNo = (currentStartSeqNo + 1) % SEQ_NO;
        }
        sendAck(dataPacket);
        lock.unlock();
        System.out.println(baseIndex);
    }
}