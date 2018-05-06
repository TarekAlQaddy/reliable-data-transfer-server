import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class GoBackN implements Runnable{

    private static File file= new File("client.in");
    private static BufferedReader reader;
    String filename;

    private static String[] inputFile = new String[5];

    private static final int BYTE_SIZE = 200;
    private static int SEQ_NO;
    private static final int PACKETS_NO = 65536;
    private static int WINDOW_SIZE;
    private static int baseIndex = 0;
    private static Packet[] recievedPackets = new Packet[PACKETS_NO];
    private static DatagramSocket socket;
    private static InetAddress address;
    private DatagramPacket datagramPacket;
    private static Lock lock = new ReentrantLock();
    private static int[] index = new int[PACKETS_NO];

    private GoBackN(DatagramPacket serverData) {
        datagramPacket = serverData;
    }

    GoBackN(String filename) throws IOException {
        this.filename = filename;
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
        WINDOW_SIZE = Integer.parseInt(inputFile[4]);
        SEQ_NO = WINDOW_SIZE;
        /*  a packet consists of : [checksum,seq_no,is_last_packet, is_ack]*/
        String s = "2&0&0&0&$" + fileName;
        for(int j = 0;j < 65536;j++){
            index[j] = j%SEQ_NO;
        }
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
            splittedServerFirstAckData = splittedServerFirstAckData[0].split("&");//            double random = 0 + Math.random() * (1 - 0);
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
                        Runnable r = new GoBackN(serverData);
                        new Thread(r).start();
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
        lock.lock();
        String temp = String.format("%02d",dataPacket.getSeq_no());
        String dataPacketAck = "&" + temp + "&" + dataPacket.getIsLastPacket() + "&" + "1&$";
        int computedChecksum = StopAndWait.computeChecksum(dataPacketAck);
        String formatted = String.format("%03d", computedChecksum);
        String sendAck = formatted + dataPacketAck;
        DatagramPacket sendDataPacketAck = new DatagramPacket(sendAck.getBytes(), sendAck.length(), address, 12345);
        socket.send(sendDataPacketAck);
        System.out.println("ack sent for item with seq_no" + dataPacket.getSeq_no());
        lock.unlock();
    }

    @Override
    public void run() {
        String packetOfData = new String(datagramPacket.getData());
        String[] recievedPacket = packetOfData.split("&");
        Packet dataPacket = StopAndWait.assignToPacket(recievedPacket, 1);
        if (StopAndWait.computeChecksum(packetOfData.substring(3)) == dataPacket.getChecksum()) {
//        System.out.println(dataPacket.getData());
//        System.out.println(dataPacket.getSeq_no());
        System.out.println(dataPacket.getSeq_no() + " ,        " + index[baseIndex]);
        System.out.println(baseIndex);
        lock.lock();
        if (index[baseIndex] == dataPacket.getSeq_no()){
//            lock.lock();
                recievedPackets[baseIndex] = dataPacket;
//                System.out.println(dataPacket.getSeq_no() + " ,        " + index[baseIndex]);
                try {
                    sendAck(dataPacket);
                } catch (IOException e) {
                    e.printStackTrace();
                }
                baseIndex++;
//                lock.unlock();
            }
            if (dataPacket.getIsLastPacket() == 1) {
                System.out.println("file well received, closing connection...");
//                    Utils.writeToFile(new ArrayList<>(Arrays.asList(recievedPackets)));
                socket.close();
                System.exit(1);
            }
        }
        lock.unlock();
    }
}
