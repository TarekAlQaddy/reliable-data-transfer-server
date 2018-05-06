import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class reciever {
    static Packet recievedRequest;
    public static void main(String[] args) throws IOException {
        DatagramSocket socket = new DatagramSocket(50000);
        InetAddress address = InetAddress.getByName("localhost");
        byte[] receiveData = new byte[500];
        while (true){
            DatagramPacket recievepacket = new DatagramPacket(receiveData,receiveData.length);
            socket.receive(recievepacket);
            String sentence = new String(recievepacket.getData());
            String[] requestParameters = sentence.split("\r");
            recievedRequest = StopAndWait.assignToPacket(requestParameters,1);
            System.out.println("Recieved: "+ sentence);
            break;
        }
        String firstAck = "000\r0\r0\r0\r0\r1\r\n";
        DatagramPacket packota = new DatagramPacket(firstAck.getBytes(),firstAck.length(),address,5000);
        socket.send(packota);



        Packet newPacket1 = recievedRequest;
        newPacket1.setData("ahlan bek ya ahmed");
        String dataPacketAck = "2\r5\r" + newPacket1.getSeq_no() + "\r" + newPacket1.getIsLastPacket() + "\r" + "1\r\n" + newPacket1.getData();
        DatagramPacket sendPacket = new DatagramPacket(dataPacketAck.getBytes(),dataPacketAck.length(),address,5000);
        socket.send(sendPacket);
        DatagramPacket dataAckRecieve = new DatagramPacket(receiveData,receiveData.length);
        socket.receive(dataAckRecieve);
        String recievedAck1 = new String (dataAckRecieve.getData());
        System.out.println(recievedAck1);

            Packet newPacket2 = recievedRequest;
            newPacket2.setData("ezayak ya m7md");
            dataPacketAck = "2\r5\r" + newPacket2.getSeq_no() + "\r" + newPacket2.getIsLastPacket() + "\r" + "1\r\n" + newPacket2.getData();
            sendPacket = new DatagramPacket(dataPacketAck.getBytes(),dataPacketAck.length(),address,5000);
            socket.send(sendPacket);
            socket.receive(dataAckRecieve);
            String recieveAck2 = new String (dataAckRecieve.getData());
            System.out.println(recieveAck2);
    }
}
